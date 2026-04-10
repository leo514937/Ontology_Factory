from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List, Optional

from .arbitration import ArbitrationResult, choose_best_candidate
from .clean_rules import CleanResult, clean_text_conservative
from .config import AppConfig
from .models.base import ModelOutput


@dataclass(frozen=True)
class PipelineOutput:
    clean_text: str
    rule_based: CleanResult
    model_arbitration: Optional[ArbitrationResult]
    model_outputs: List[ModelOutput]


def _split_text_into_chunks(text: str, max_chars: int) -> List[str]:
    if max_chars <= 0 or len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    def flush_current() -> None:
        nonlocal current, current_len
        if current:
            chunks.append("\n\n".join(current).strip() + "\n")
            current = []
            current_len = 0

    for paragraph in paragraphs:
        para = paragraph.strip()
        if not para:
            continue
        if len(para) > max_chars:
            flush_current()
            for index in range(0, len(para), max_chars):
                piece = para[index : index + max_chars].strip()
                if piece:
                    chunks.append(piece + "\n")
            continue

        separator_len = 2 if current else 0
        if current_len + separator_len + len(para) > max_chars:
            flush_current()
        current.append(para)
        current_len += len(para) + (2 if len(current) > 1 else 0)

    flush_current()
    return chunks if chunks else [text]


def _run_models_once(input_text: str, cfg: AppConfig, scope: str) -> tuple[List[ModelOutput], ArbitrationResult]:
    def _run_single(candidate) -> ModelOutput:
        if candidate.provider != "openai_compat":
            raise ValueError(f"Unsupported provider: {candidate.provider}")
        from .models import OpenAICompatClient

        print(
            f"[MODEL_START] scope={scope} name={candidate.name} "
            f"model={candidate.model} timeout_s={candidate.timeout_s}"
        )
        client = OpenAICompatClient(
            name=candidate.name,
            base_url=candidate.base_url,
            api_key_env=candidate.api_key_env,
            model=candidate.model,
            timeout_s=candidate.timeout_s,
        )
        return client.clean_text(input_text)

    model_outputs: List[ModelOutput] = []
    model_failures: list[str] = []
    submit_times: dict = {}
    max_workers = max(1, len(cfg.models.candidates))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_candidate = {}
        for candidate in cfg.models.candidates:
            future = executor.submit(_run_single, candidate)
            future_to_candidate[future] = candidate
            submit_times[future] = time.perf_counter()
        for future in as_completed(future_to_candidate):
            candidate = future_to_candidate[future]
            started = submit_times[future]
            try:
                output = future.result()
            except Exception as exc:
                elapsed = time.perf_counter() - started
                print(
                    f"[MODEL_ERR] scope={scope} name={candidate.name} "
                    f"elapsed_s={elapsed:.2f} error={type(exc).__name__}: {exc}"
                )
                model_failures.append(f"{candidate.name}:{type(exc).__name__}:{exc}")
                continue
            elapsed = time.perf_counter() - started
            print(
                f"[MODEL_OK] scope={scope} name={candidate.name} "
                f"elapsed_s={elapsed:.2f} confidence={output.confidence}"
            )
            model_outputs.append(output)

    if len(model_outputs) < 2:
        failure_text = "; ".join(model_failures) if model_failures else "unknown"
        raise RuntimeError(
            f"Insufficient successful model runs in {scope}: success={len(model_outputs)} "
            f"required>=2 failures=[{failure_text}]"
        )

    arbitration = choose_best_candidate(input_text, model_outputs, cfg.models.arbitration)
    print(
        f"[ARBITRATION] scope={scope} chosen={arbitration.chosen_name} "
        f"rationale={arbitration.rationale} rejected={len(arbitration.rejected)}"
    )
    return model_outputs, arbitration


def _summarize_outputs(outputs: List[ModelOutput]) -> List[ModelOutput]:
    grouped: Dict[str, List[ModelOutput]] = {}
    for output in outputs:
        grouped.setdefault(output.name, []).append(output)

    summary: List[ModelOutput] = []
    for name, items in grouped.items():
        average_confidence = sum(item.confidence for item in items) / max(1, len(items))
        summary.append(
            ModelOutput(
                name=name,
                cleaned_text="",
                confidence=average_confidence,
                notes=f"chunks_succeeded={len(items)}",
            )
        )
    return sorted(summary, key=lambda item: item.name)


def run_pipeline(text: str, cfg: AppConfig) -> PipelineOutput:
    rule_result = clean_text_conservative(text) if cfg.pipeline.conservative else CleanResult(text, 0, 0)  # type: ignore[arg-type]
    print(
        f"[RULE] input_chars={len(text)} clean_chars={len(rule_result.clean_text)} "
        f"removed_lines={rule_result.removed_lines} merged_wrap={rule_result.merged_wrap_lines}"
    )

    model_outputs: List[ModelOutput] = []
    arbitration: Optional[ArbitrationResult] = None

    if cfg.models.enabled and cfg.models.candidates:
        use_chunking = cfg.models.chunking.enabled and len(rule_result.clean_text) > cfg.models.chunking.max_chars
        if use_chunking:
            chunks = _split_text_into_chunks(rule_result.clean_text, cfg.models.chunking.max_chars)
            print(
                f"[CHUNK] enabled=True max_chars={cfg.models.chunking.max_chars} "
                f"total_chunks={len(chunks)}"
            )

            all_outputs: List[ModelOutput] = []
            chunk_cleaned: List[str] = []
            rejected: List[str] = []
            chosen_names: List[str] = []

            for index, chunk in enumerate(chunks, start=1):
                scope = f"chunk_{index}/{len(chunks)}"
                print(f"[CHUNK_START] scope={scope} chars={len(chunk)}")
                outputs, chunk_arbitration = _run_models_once(chunk, cfg, scope=scope)
                all_outputs.extend(outputs)
                chosen_names.append(chunk_arbitration.chosen_name)
                rejected.extend(f"{scope}:{item}" for item in chunk_arbitration.rejected)
                chunk_cleaned.append(chunk_arbitration.clean_text.strip("\n"))

            clean_text = ("\n\n".join(chunk_cleaned)).rstrip() + "\n"
            model_outputs = _summarize_outputs(all_outputs)
            arbitration = ArbitrationResult(
                chosen_name=f"chunked({len(chunks)})",
                clean_text=clean_text,
                rationale=f"chunked_arbitration:{'|'.join(chosen_names)}",
                rejected=rejected,
            )
            print(f"[CHUNK_DONE] total_chunks={len(chunks)} output_chars={len(clean_text)}")
        else:
            model_outputs, arbitration = _run_models_once(rule_result.clean_text, cfg, scope="full_text")
            clean_text = arbitration.clean_text
    else:
        print("[ARBITRATION] skipped=models_disabled_or_empty")
        clean_text = rule_result.clean_text

    return PipelineOutput(
        clean_text=clean_text,
        rule_based=rule_result,
        model_arbitration=arbitration,
        model_outputs=model_outputs,
    )
