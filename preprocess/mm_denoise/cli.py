from __future__ import annotations

import argparse
import contextlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import load_config
from .io_loaders import discover_inputs, load_document, normalize_text_for_pipeline
from .pipeline import run_pipeline

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.no_models.yaml"


def _write_output(out_dir: Path, input_path: Path, clean_text: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{input_path.stem}.clean.txt"
    output_path.write_text(clean_text, encoding="utf-8")
    return output_path


def _write_report(out_dir: Path, input_path: Path, out_path: Path, pipeline_out) -> Path:
    report_path = out_dir / f"{input_path.stem}.report.json"
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "path": str(input_path),
            "suffix": input_path.suffix.lower(),
        },
        "output": {
            "clean_text_path": str(out_path),
            "report_path": str(report_path),
        },
        "rules": {
            "removed_lines": pipeline_out.rule_based.removed_lines,
            "merged_wrap_lines": pipeline_out.rule_based.merged_wrap_lines,
        },
        "models": {
            "enabled": pipeline_out.model_arbitration is not None,
            "candidates": [
                {
                    "name": item.name,
                    "confidence": item.confidence,
                    "notes": item.notes,
                }
                for item in pipeline_out.model_outputs
            ],
        },
        "arbitration": None,
    }
    if pipeline_out.model_arbitration is not None:
        report["arbitration"] = {
            "chosen_name": pipeline_out.model_arbitration.chosen_name,
            "rationale": pipeline_out.model_arbitration.rationale,
            "rejected": pipeline_out.model_arbitration.rejected,
        }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-model conservative document denoiser (clean text only).")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to config.yaml")
    parser.add_argument("--input", default=None, help="Single input file path. If omitted, use io.input_globs.")
    parser.add_argument("--base-dir", default=".", help="Base directory for glob discovery.")
    parser.add_argument("--output-dir", default="", help="Optional output directory override.")
    parser.add_argument("--stdout-json", action="store_true", help="Print a machine-readable JSON summary.")
    args = parser.parse_args()

    config = load_config(args.config)
    inputs = [args.input] if args.input else discover_inputs(config.io.input_globs, args.base_dir)
    if not inputs:
        raise SystemExit("No input files found.")

    output_dir = Path(args.output_dir).resolve() if args.output_dir else (Path(args.base_dir) / config.io.output_dir)
    results: list[dict[str, object]] = []

    for input_item in inputs:
        document = load_document(input_item, config.io.encoding_fallbacks)
        raw_text = normalize_text_for_pipeline(document.text)
        if args.stdout_json:
            with contextlib.redirect_stdout(io.StringIO()):
                pipeline_output = run_pipeline(raw_text, config)
        else:
            print(f"[START] input={document.path}")
            print(f"[TEXT] raw_chars={len(raw_text)} raw_lines={raw_text.count(chr(10)) + 1}")
            print(f"[MODELS] enabled={config.models.enabled} candidates={len(config.models.candidates)}")
            pipeline_output = run_pipeline(raw_text, config)

        clean_text_path = _write_output(output_dir, document.path, pipeline_output.clean_text)
        report_path = _write_report(output_dir, document.path, clean_text_path, pipeline_output)
        result_item = {
            "input_path": str(document.path),
            "clean_text_path": str(clean_text_path),
            "report_path": str(report_path),
        }
        results.append(result_item)

        if not args.stdout_json:
            print(f"[OK] {document.path} -> {clean_text_path}")
            if pipeline_output.model_arbitration is not None:
                print(
                    "     chosen="
                    f"{pipeline_output.model_arbitration.chosen_name} "
                    f"reason={pipeline_output.model_arbitration.rationale}"
                )
            print(
                "     rule_removed_lines="
                f"{pipeline_output.rule_based.removed_lines} "
                f"rule_merged_wrap={pipeline_output.rule_based.merged_wrap_lines}"
            )
            print(f"     report={report_path}")

    if args.stdout_json:
        print(
            json.dumps(
                {
                    "config_path": str(Path(args.config).resolve()),
                    "results": results,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
