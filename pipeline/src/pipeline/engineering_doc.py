from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from pipeline.bootstrap import ensure_local_imports, workspace_root
from pipeline.config import load_pipeline_config

ensure_local_imports()

from entity_relation import extract_relations
from ner import OpenRouterClient, OpenRouterConfig, extract_entities
from ner.providers.hanlp_provider import HanLPNerProvider
from ontology_core.cli import search_canonical_entities
from ontology_store import OntologyStore
from ontology_store.cli import query_store
from xiaogugit import XiaoGuGitManager


class EngineeringDocRunResult(BaseModel):
    input_path: str
    clean_text_path: str
    preprocess_report_path: str
    ner_output_path: str
    relation_output_path: str
    ontology_core_output_path: str
    ontology_store_output_path: str
    structured_output_path: str
    xiaogugit_write_result_path: str
    read_result_path: str
    version_tree_result_path: str
    report_path: str
    store_path: str
    xiaogugit_root: str
    project_id: str
    filename: str


_COMMAND_RE = re.compile(r"(?mi)^\s*(python\s+.+)$")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？；\n])")
_GOAL_KEYWORDS = ("目标", "用于", "实现", "支持", "负责", "提供", "连接", "上传", "监测", "控制", "处理")
_RISK_KEYWORDS = ("风险", "待确认", "TODO", "未", "可能", "建议", "缺少")


def run_engineering_doc_pipeline(
    input_path: str,
    *,
    preprocess_config: str | None = None,
    pipeline_config: str | None = None,
    xiaogugit_root: str | None = None,
    project_id: str | None = None,
    filename: str | None = None,
    document_title: str | None = None,
) -> EngineeringDocRunResult:
    config = load_pipeline_config(pipeline_config)
    input_file = Path(input_path).resolve()
    clean_config_path = Path(
        preprocess_config or (workspace_root() / "preprocess" / "config.no_models.yaml")
    ).resolve()
    artifact_dir = _artifact_dir(config.output.root_dir, input_file)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    clean_text, preprocess_report = _run_preprocess(input_file, clean_config_path)
    clean_text_path = artifact_dir / "clean_text.txt"
    preprocess_report_path = artifact_dir / "preprocess_report.json"
    clean_text_path.write_text(clean_text, encoding="utf-8")
    _write_json(preprocess_report_path, preprocess_report)

    llm_client = OpenRouterClient(OpenRouterConfig.from_mapping(config.llm))
    provider = HanLPNerProvider(model_name=config.ner.model_name)
    ner_document = extract_entities(
        clean_text,
        doc_id=input_file.stem,
        use_llm=config.ner.use_llm,
        provider=provider,
        llm_client=llm_client,
    )
    ner_output_path = artifact_dir / "ner_output.json"
    ner_output_path.write_text(ner_document.model_dump_json(indent=2), encoding="utf-8")

    relation_document = extract_relations(ner_document)
    relation_output_path = artifact_dir / "entity_relation_output.json"
    relation_output_path.write_text(relation_document.model_dump_json(indent=2), encoding="utf-8")

    store = OntologyStore(config.storage.database_path)
    ontology_core_payload = _query_ontology_core(store, ner_document)
    ontology_core_output_path = artifact_dir / "ontology_core_output.json"
    _write_json(ontology_core_output_path, ontology_core_payload)

    fallback_reason = ""
    ontology_store_fallback_used = ontology_core_payload["total_items"] == 0
    if ontology_core_payload["total_items"] < min(2, max(1, len(ner_document.entities))):
        ontology_store_fallback_used = True
        fallback_reason = "ontology_core结果为空或不足以支撑层次化整理"
    ontology_store_payload = _query_ontology_store(
        store,
        document_title or input_file.stem,
        ner_document,
        fallback_reason=fallback_reason,
    )
    ontology_store_output_path = artifact_dir / "ontology_store_output.json"
    _write_json(ontology_store_output_path, ontology_store_payload)

    structured_payload = _build_structured_payload(
        input_file=input_file,
        clean_text=clean_text,
        clean_text_path=clean_text_path,
        ner_document=ner_document,
        relation_document=relation_document,
        ontology_core_payload=ontology_core_payload,
        ontology_store_payload=ontology_store_payload,
        document_title=document_title or input_file.stem,
        query_strategy={
            "ontology_core_total_items": ontology_core_payload["total_items"],
            "ontology_store_fallback_used": ontology_store_fallback_used,
            "fallback_reason": fallback_reason or ("ontology_core命中充足" if not ontology_store_fallback_used else "手动补充查询"),
        },
    )
    structured_output_path = artifact_dir / f"清洗后的{input_file.stem}结构化结果.json"
    _write_json(structured_output_path, structured_payload)

    resolved_xiaogugit_root = Path(xiaogugit_root or (workspace_root() / "xiaogugit" / "storage")).resolve()
    resolved_project_id = project_id or _safe_slug(input_file.stem)
    resolved_filename = filename or f"{_safe_slug(input_file.stem)}.structured.json"

    manager = XiaoGuGitManager(root_dir=str(resolved_xiaogugit_root))
    if not manager._repo_exists(resolved_project_id):
        manager.init_project(
            resolved_project_id,
            name=document_title or input_file.stem,
            description="工程文档结构化入库项目",
        )

    write_result = manager.write_version(
        resolved_project_id,
        resolved_filename,
        structured_payload,
        f"AI: ingest engineering doc {document_title or input_file.stem}",
        "engineering-doc-pipeline",
        "Codex",
        "auto",
    )
    read_result = {"data": manager.read_version(resolved_project_id, resolved_filename)}
    version_tree = manager.get_file_version_tree(resolved_project_id, resolved_filename)

    write_result_path = artifact_dir / "xiaogugit_write_result.json"
    read_result_path = artifact_dir / "xiaogugit_read_result.json"
    version_tree_result_path = artifact_dir / "xiaogugit_version_tree.json"
    _write_json(write_result_path, write_result)
    _write_json(read_result_path, read_result)
    _write_json(version_tree_result_path, version_tree)

    report_path = artifact_dir / "engineering_doc_report.json"
    _write_json(
        report_path,
        {
            "input_path": str(input_file),
            "clean_text_path": str(clean_text_path),
            "ner_output_path": str(ner_output_path),
            "relation_output_path": str(relation_output_path),
            "ontology_core_output_path": str(ontology_core_output_path),
            "ontology_store_output_path": str(ontology_store_output_path),
            "structured_output_path": str(structured_output_path),
            "xiaogugit_root": str(resolved_xiaogugit_root),
            "project_id": resolved_project_id,
            "filename": resolved_filename,
            "write_result": write_result,
            "version_tree_latest": version_tree.get("latest_version_id"),
        },
    )

    return EngineeringDocRunResult(
        input_path=str(input_file),
        clean_text_path=str(clean_text_path),
        preprocess_report_path=str(preprocess_report_path),
        ner_output_path=str(ner_output_path),
        relation_output_path=str(relation_output_path),
        ontology_core_output_path=str(ontology_core_output_path),
        ontology_store_output_path=str(ontology_store_output_path),
        structured_output_path=str(structured_output_path),
        xiaogugit_write_result_path=str(write_result_path),
        read_result_path=str(read_result_path),
        version_tree_result_path=str(version_tree_result_path),
        report_path=str(report_path),
        store_path=str(Path(config.storage.database_path).resolve()),
        xiaogugit_root=str(resolved_xiaogugit_root),
        project_id=resolved_project_id,
        filename=resolved_filename,
    )


def _artifact_dir(output_root: str, input_file: Path) -> Path:
    digest = hashlib.sha1(input_file.read_bytes()).hexdigest()[:8]
    safe_stem = _safe_slug(input_file.stem)
    return Path(output_root).expanduser().resolve() / "engineering_doc" / f"{safe_stem}_{digest}"


def _run_preprocess(input_file: Path, config_path: Path) -> tuple[str, dict[str, Any]]:
    from mm_denoise.config import load_config
    from mm_denoise.io_loaders import load_document, normalize_text_for_pipeline
    from mm_denoise.pipeline import run_pipeline

    config = load_config(str(config_path))
    document = load_document(str(input_file), config.io.encoding_fallbacks)
    raw_text = normalize_text_for_pipeline(document.text)
    output = run_pipeline(raw_text, config)
    report = {
        "input_path": str(document.path),
        "config_path": str(config_path),
        "rule_removed_lines": output.rule_based.removed_lines,
        "rule_merged_wrap_lines": output.rule_based.merged_wrap_lines,
        "model_candidates": [
            {
                "name": item.name,
                "confidence": item.confidence,
                "notes": item.notes,
            }
            for item in output.model_outputs
        ],
        "model_arbitration": output.model_arbitration.chosen_name if output.model_arbitration else None,
    }
    return output.clean_text, report


def _query_ontology_core(store: OntologyStore, ner_document) -> dict[str, Any]:
    queries = []
    total_items = 0
    seen: set[str] = set()
    for entity in ner_document.entities:
        query = (entity.normalized_text or entity.text).strip()
        if not query or query in seen:
            continue
        seen.add(query)
        payload = search_canonical_entities(
            store,
            query=query,
            limit=3,
            include_mentions=True,
            include_relations=True,
        )
        queries.append(payload)
        total_items += int(payload.get("count", 0))
        if len(queries) >= 8:
            break
    return {
        "queries": queries,
        "total_items": total_items,
    }


def _query_ontology_store(
    store: OntologyStore,
    document_title: str,
    ner_document,
    *,
    fallback_reason: str,
) -> dict[str, Any]:
    query_text = document_title.strip()
    if not query_text and ner_document.entities:
        query_text = ner_document.entities[0].normalized_text or ner_document.entities[0].text
    primary = query_store(store, kind="entities", query=query_text, limit=10)
    return {
        **primary,
        "primary_query": query_text,
        "fallback_reason": fallback_reason,
        "supplemental": {
            "relations": query_store(store, kind="relations", query=query_text, limit=10),
            "classifications": query_store(store, kind="classifications", query=query_text, limit=10),
        },
    }


def _build_structured_payload(
    *,
    input_file: Path,
    clean_text: str,
    clean_text_path: Path,
    ner_document,
    relation_document,
    ontology_core_payload: dict[str, Any],
    ontology_store_payload: dict[str, Any],
    document_title: str,
    query_strategy: dict[str, Any],
) -> dict[str, Any]:
    sentences = _split_sentences(clean_text)
    commands = [match.group(1).strip() for match in _COMMAND_RE.finditer(clean_text)]
    components = _system_components(ner_document.entities)
    responsibilities = _module_responsibilities(relation_document.relations)
    data_flow = _data_flow(relation_document.relations)
    interfaces = _interfaces_and_dependencies(commands, ner_document.entities)
    risks = _risks_and_open_questions(sentences)
    layers = _build_ontology_layers(ner_document.entities, relation_document.relations, commands, document_title)
    ontology_entities = [item for layer_items in layers.values() for item in layer_items]
    ontology_relations = _build_ontology_relations(
        ner_document.entities,
        relation_document.relations,
        ontology_core_payload,
        layers,
    )
    evidence = _build_evidence(
        input_file=input_file,
        clean_text_path=clean_text_path,
        sentences=sentences,
        ner_document=ner_document,
        relation_document=relation_document,
    )
    goals = [sentence for sentence in sentences if any(keyword in sentence for keyword in _GOAL_KEYWORDS)]
    if not goals and sentences:
        goals = sentences[:2]

    return {
        "source_path": str(input_file),
        "clean_text_path": str(clean_text_path),
        "document_title": document_title,
        "project_background": {
            "title": document_title,
            "summary": " ".join(sentences[:2]).strip() or document_title,
            "source_excerpt": sentences[0] if sentences else "",
        },
        "system_goals": goals[:6],
        "system_components": components,
        "module_responsibilities": responsibilities,
        "data_flow_or_process_flow": data_flow,
        "interfaces_commands_dependencies": interfaces,
        "ontology_layers": layers,
        "ontology_entities": ontology_entities,
        "ontology_relations": ontology_relations,
        "risks_and_open_questions": risks,
        "query_strategy": query_strategy,
        "evidence": evidence,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_outputs": {
            "ner_output": "ner_output.json",
            "relation_output": "entity_relation_output.json",
            "ontology_core_output": "ontology_core_output.json",
            "ontology_store_output": "ontology_store_output.json",
        },
    }


def _split_sentences(text: str) -> list[str]:
    return [piece.strip() for piece in _SENTENCE_SPLIT_RE.split(text) if piece.strip()]


def _system_components(entities) -> list[dict[str, Any]]:
    results = []
    for entity in entities:
        normalized = (entity.normalized_text or entity.text).strip()
        if not normalized:
            continue
        results.append(
            {
                "name": normalized,
                "label": entity.label,
                "description": entity.source_sentence,
                "evidence": entity.metadata.get("source_sentences", [])[:2] or [entity.source_sentence],
            }
        )
    return results[:12]


def _module_responsibilities(relations) -> list[dict[str, Any]]:
    results = []
    for relation in relations:
        results.append(
            {
                "module": relation.source_text,
                "responsibility": f"{relation.relation_type} {relation.target_text}",
                "evidence": relation.evidence_sentence,
            }
        )
    return results[:12]


def _data_flow(relations) -> list[dict[str, Any]]:
    results = []
    for index, relation in enumerate(relations, start=1):
        results.append(
            {
                "step": index,
                "from": relation.source_text,
                "relation": relation.relation_type,
                "to": relation.target_text,
                "evidence": relation.evidence_sentence,
            }
        )
    return results[:12]


def _interfaces_and_dependencies(commands: list[str], entities) -> list[dict[str, Any]]:
    results = [{"kind": "command", "value": command, "evidence": command} for command in commands]
    for entity in entities:
        normalized = (entity.normalized_text or entity.text).strip()
        if not normalized:
            continue
        if entity.label.upper() in {"TECH", "DEVICE", "SERVICE", "API"} or any(
            keyword in normalized.lower() for keyword in ("api", "net", "cloud", "mqtt", "http", "service", "platform")
        ):
            results.append(
                {
                    "kind": "dependency",
                    "value": normalized,
                    "label": entity.label,
                    "evidence": entity.source_sentence,
                }
            )
    return results[:16]


def _risks_and_open_questions(sentences: list[str]) -> list[str]:
    items = [sentence for sentence in sentences if any(keyword in sentence for keyword in _RISK_KEYWORDS)]
    if items:
        return items[:6]
    return ["待确认：原文未明确列出风险项或开放问题。"]


def _build_ontology_layers(entities, relations, commands: list[str], document_title: str) -> dict[str, list[dict[str, Any]]]:
    l0 = [
        _record("L0", "Upper", "对象", None, "工程语境中的稳定实体、组件或资源。", ["name", "category"]),
        _record("L0", "Upper", "过程", None, "工程中的动作、流程或处理步骤。", ["step", "actor"]),
        _record("L0", "Upper", "接口", None, "对外暴露的调用入口、命令或协议边界。", ["command", "parameters"]),
        _record("L0", "Upper", "约束", None, "工程中的限制、风险或待确认事项。", ["risk", "status"]),
    ]
    l1 = [
        _record("L1", "General_Domain", "工程项目", "对象", "当前工程文档所描述的系统或项目。", ["title", "scope"]),
        _record("L1", "General_Domain", "系统组件", "对象", "系统内部的模块、设备或技术组件。", ["label", "occurrence_count"]),
        _record("L1", "General_Domain", "外部依赖", "对象", "系统接入的平台、服务或外部资源。", ["service_type", "protocol"]),
        _record("L1", "General_Domain", "数据流程", "过程", "系统内的数据流和处理流程。", ["source", "target", "relation"]),
        _record("L1", "General_Domain", "接口命令", "接口", "文档中出现的命令或调用入口。", ["command", "args"]),
        _record("L1", "General_Domain", "风险项", "约束", "待确认问题或潜在风险。", ["risk", "evidence"]),
    ]
    l2 = [
        _record("L2", "Sub_Domain", "项目主题", "工程项目", "贴近当前文档主题的项目级概念。", ["document_title"]),
        _record("L2", "Sub_Domain", "技术组件类型", "系统组件", "技术模块、设备或软硬件构件。", ["label", "source_sentence"]),
        _record("L2", "Sub_Domain", "外部平台类型", "外部依赖", "云平台、服务或协议依赖。", ["label", "source_sentence"]),
        _record("L2", "Sub_Domain", "流程关系类型", "数据流程", "文档中显式出现的流程关系。", ["relation_type", "evidence"]),
    ]
    if commands:
        l2.append(_record("L2", "Sub_Domain", "命令入口类型", "接口命令", "可执行命令或 CLI 入口。", ["command"]))

    l3 = [
        _record(
            "L3",
            "Application",
            document_title,
            "项目主题",
            "来自工程文本的项目级实例。",
            ["source_path", "document_title"],
            {"document_title": document_title},
        )
    ]
    for entity in entities:
        normalized = (entity.normalized_text or entity.text).strip()
        if not normalized:
            continue
        parent = "技术组件类型"
        if any(keyword in normalized.lower() for keyword in ("api", "net", "cloud", "service", "platform")):
            parent = "外部平台类型"
        elif entity.label.upper() not in {"TECH", "DEVICE", "SERVICE"}:
            parent = "项目主题"
        l3.append(
            _record(
                "L3",
                "Application",
                normalized,
                parent,
                entity.source_sentence or "来自工程文本的实体实例。",
                ["label", "occurrence_count", "source_sentence"],
                {
                    "entity_id": entity.entity_id,
                    "label": entity.label,
                    "occurrence_count": entity.metadata.get("occurrence_count", 1),
                    "source_sentence": entity.source_sentence,
                },
            )
        )
    for command in commands:
        l3.append(
            _record(
                "L3",
                "Application",
                command,
                "命令入口类型",
                "来自工程文本的命令实例。",
                ["command"],
                {"command": command},
            )
        )
    for relation in relations[:8]:
        l3.append(
            _record(
                "L3",
                "Application",
                f"{relation.source_text}->{relation.relation_type}->{relation.target_text}",
                "流程关系类型",
                relation.evidence_sentence,
                ["relation_type", "evidence_sentence"],
                {
                    "relation_id": relation.relation_id,
                    "relation_type": relation.relation_type,
                    "source_text": relation.source_text,
                    "target_text": relation.target_text,
                },
            )
        )
    return {"L0": l0, "L1": l1, "L2": l2, "L3": l3}


def _build_ontology_relations(entities, relations, ontology_core_payload: dict[str, Any], layers: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    results = [
        {
            "relation_type": "belongs_to",
            "source_concept": "工程项目",
            "target_concept": "对象",
            "source_layer": "L1",
            "target_layer": "L0",
            "evidence": "结构化建模规则",
            "source": "derived",
        },
        {
            "relation_type": "belongs_to",
            "source_concept": "系统组件",
            "target_concept": "对象",
            "source_layer": "L1",
            "target_layer": "L0",
            "evidence": "结构化建模规则",
            "source": "derived",
        },
    ]
    for entity in entities:
        normalized = (entity.normalized_text or entity.text).strip()
        if not normalized:
            continue
        results.append(
            {
                "relation_type": "instantiates",
                "source_concept": normalized,
                "target_concept": "技术组件类型",
                "source_layer": "L3",
                "target_layer": "L2",
                "evidence": entity.source_sentence,
                "source": "ner",
            }
        )
    for relation in relations:
        results.append(
            {
                "relation_type": relation.relation_type,
                "source_concept": relation.source_text,
                "target_concept": relation.target_text,
                "source_layer": "L3",
                "target_layer": "L3",
                "evidence": relation.evidence_sentence,
                "source": "entity-relation",
            }
        )
    for query_payload in ontology_core_payload.get("queries", []):
        query = query_payload.get("query", "")
        for item in query_payload.get("items", []):
            entity = item.get("entity", {})
            preferred_name = entity.get("preferred_name") or entity.get("normalized_text")
            if query and preferred_name:
                results.append(
                    {
                        "relation_type": "matches_canonical",
                        "source_concept": query,
                        "target_concept": preferred_name,
                        "source_layer": "L3",
                        "target_layer": "L3",
                        "evidence": "ontology-core",
                        "source": "ontology-core",
                    }
                )
    return results


def _build_evidence(*, input_file: Path, clean_text_path: Path, sentences: list[str], ner_document, relation_document) -> list[dict[str, Any]]:
    evidence = [
        {
            "source": "clean_text",
            "path": str(clean_text_path),
            "excerpt": sentences[:3],
        }
    ]
    for entity in ner_document.entities[:12]:
        evidence.append(
            {
                "source": "ner",
                "path": str(input_file),
                "entity_id": entity.entity_id,
                "text": entity.text,
                "label": entity.label,
                "excerpt": entity.source_sentence,
            }
        )
    for relation in relation_document.relations[:12]:
        evidence.append(
            {
                "source": "entity-relation",
                "path": str(input_file),
                "relation_id": relation.relation_id,
                "relation_type": relation.relation_type,
                "excerpt": relation.evidence_sentence,
            }
        )
    return evidence


def _record(
    layer: str,
    type_name: str,
    concept: str,
    parent_concept: str | None,
    description: str,
    attributes: list[str],
    instance_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "layer": layer,
        "type": type_name,
        "concept": concept,
        "parent_concept": parent_concept,
        "description": description,
        "attributes": attributes,
        "instance_data": instance_data,
    }


def _safe_slug(value: str) -> str:
    rendered = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return rendered.strip("_") or "engineering_doc"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
