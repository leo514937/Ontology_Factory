from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_ENV_VAR = "ONTOLOGY_FACTORY_QAGENT_CONFIG"
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "qagent.local.toml"


@dataclass(frozen=True)
class UnifiedLlmConfig:
    enabled: bool = False
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    timeout_s: float = 60.0

    def is_configured(self) -> bool:
        return self.enabled and bool(self.base_url and self.api_key and self.model)


def default_config_path() -> Path:
    return DEFAULT_CONFIG_PATH


def resolve_config_path(config_path: str | Path | None = None) -> Path:
    raw = config_path or os.environ.get(CONFIG_ENV_VAR, "").strip() or str(DEFAULT_CONFIG_PATH)
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (REPO_ROOT / path).resolve()
    return path


def load_qagent_config(config_path: str | Path | None = None) -> dict[str, Any]:
    path = resolve_config_path(config_path)
    if not path.exists():
        return {}
    with path.open("rb") as fh:
        payload = tomllib.load(fh)
    return payload if isinstance(payload, dict) else {}


def resolve_unified_llm_config(config_path: str | Path | None = None) -> UnifiedLlmConfig:
    payload = load_qagent_config(config_path)
    llm_payload = payload.get("llm") or payload.get("default_llm") or {}
    if not isinstance(llm_payload, dict):
        return UnifiedLlmConfig()
    return UnifiedLlmConfig(
        enabled=bool(llm_payload.get("enabled", True)),
        base_url=str(llm_payload.get("base_url", "")).strip(),
        api_key=str(llm_payload.get("api_key", "")).strip(),
        model=str(llm_payload.get("model", "")).strip(),
        timeout_s=float(llm_payload.get("timeout_s", 60.0)),
    )


def apply_unified_llm_env(
    existing: dict[str, str] | None = None,
    *,
    config_path: str | Path | None = None,
) -> dict[str, str]:
    env = dict(existing or os.environ)
    resolved_config_path = resolve_config_path(config_path)
    env[CONFIG_ENV_VAR] = str(resolved_config_path)
    llm = resolve_unified_llm_config(resolved_config_path)
    if not llm.is_configured():
        return env

    env.update(
        {
            "OPENROUTER_API_KEY": llm.api_key,
            "OPENROUTER_BASE_URL": llm.base_url,
            "OPENROUTER_MODEL": llm.model,
            "OPENAI_API_KEY": llm.api_key,
            "OPENAI_BASE_URL": llm.base_url,
            "ONTOLOGY_OPENAI_API_KEY": llm.api_key,
            "ONTOLOGY_OPENAI_BASE_URL": llm.base_url,
            "ONTOLOGY_OPENAI_MODEL": llm.model,
            "ONTOLOGY_AUDIT_LLM_ENABLED": "true",
            "ONTOLOGY_AUDIT_LLM_MODEL": llm.model,
        }
    )
    return env


def overlay_pipeline_llm_config(
    payload: dict[str, Any] | None,
    *,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    merged = dict(payload or {})
    llm = resolve_unified_llm_config(config_path)
    if not llm.is_configured():
        return merged
    merged.update(
        {
            "enabled": True,
            "api_key": llm.api_key,
            "api_key_env": "OPENROUTER_API_KEY",
            "base_url": llm.base_url,
            "model": llm.model,
            "model_env": "OPENROUTER_MODEL",
            "ontology_model": llm.model,
            "ontology_base_url": llm.base_url,
            "ontology_model_env": "ONTOLOGY_OPENAI_MODEL",
            "timeout_s": llm.timeout_s,
        }
    )
    return merged
