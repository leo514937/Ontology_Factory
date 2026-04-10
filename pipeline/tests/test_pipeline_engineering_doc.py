from __future__ import annotations

import json
from pathlib import Path

import yaml
from ner.providers.base import RawEntityMention

from pipeline.runner import run_engineering_doc_pipeline


def _write_preprocess_config(path: Path) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "pipeline": {"conservative": True, "output": "clean_text"},
                "io": {"input_globs": ["*.txt"], "output_dir": "outputs", "encoding_fallbacks": ["utf-8"]},
                "models": {"enabled": False, "candidates": []},
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def _write_pipeline_config(path: Path, preprocess_config: Path, store_path: Path, output_root: Path) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "preprocess": {"config_path": str(preprocess_config)},
                "ner": {"provider": "hanlp", "model_name": "unused", "use_llm": False},
                "llm": {"enabled": False},
                "dls": {"config_path": str(path.parent / "unused.toml"), "artifact_root": "", "max_concurrency": 1},
                "output": {"root_dir": str(output_root), "enable_cooccurrence_edges": False},
                "storage": {"enabled": True, "database_path": str(store_path)},
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


class DeterministicProvider:
    def __init__(self, model_name: str = "unused") -> None:
        self.model_name = model_name

    def extract(self, text: str):
        mentions: list[RawEntityMention] = []
        for term, label in [
            ("智能养鱼系统", "TERM"),
            ("ESP8266", "TECH"),
            ("OneNet", "TECH"),
            ("溶氧传感器", "DEVICE"),
        ]:
            start = text.find(term)
            if start >= 0:
                mentions.append(
                    RawEntityMention(
                        text=term,
                        label=label,
                        start=start,
                        end=start + len(term),
                        confidence=0.9,
                    )
                )
        return mentions


def test_run_engineering_doc_pipeline_generates_structured_output_and_writes_xiaogugit(
    monkeypatch,
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "fishhome.txt"
    input_path.write_text(
        "智能养鱼系统使用 ESP8266 连接 OneNet。溶氧传感器持续监测鱼缸溶氧并上传数据。",
        encoding="utf-8",
    )
    preprocess_config = tmp_path / "preprocess.yaml"
    pipeline_config = tmp_path / "pipeline.yaml"
    _write_preprocess_config(preprocess_config)
    _write_pipeline_config(
        pipeline_config,
        preprocess_config,
        tmp_path / "store.sqlite3",
        tmp_path / "pipeline_outputs",
    )

    monkeypatch.setattr("pipeline.runner.HanLPNerProvider", DeterministicProvider)
    monkeypatch.setattr("pipeline.engineering_doc.HanLPNerProvider", DeterministicProvider)

    result = run_engineering_doc_pipeline(
        str(input_path),
        preprocess_config=str(preprocess_config),
        pipeline_config=str(pipeline_config),
        xiaogugit_root=str(tmp_path / "xiaogugit_storage"),
    )

    structured = json.loads(Path(result.structured_output_path).read_text(encoding="utf-8"))
    read_back = json.loads(Path(result.read_result_path).read_text(encoding="utf-8"))
    version_tree = json.loads(Path(result.version_tree_result_path).read_text(encoding="utf-8"))
    ontology_store_payload = json.loads(Path(result.ontology_store_output_path).read_text(encoding="utf-8"))

    assert Path(result.clean_text_path).exists()
    assert Path(result.ner_output_path).exists()
    assert Path(result.relation_output_path).exists()
    assert Path(result.ontology_core_output_path).exists()
    assert Path(result.ontology_store_output_path).exists()
    assert structured["ontology_layers"]["L0"]
    assert "L1" in structured["ontology_layers"]
    assert "L2" in structured["ontology_layers"]
    assert "L3" in structured["ontology_layers"]
    assert structured["query_strategy"]["ontology_store_fallback_used"] is True
    assert ontology_store_payload["kind"] == "entities"
    assert read_back["data"]["document_title"] == structured["document_title"]
    assert version_tree["latest_version_id"] == 1
