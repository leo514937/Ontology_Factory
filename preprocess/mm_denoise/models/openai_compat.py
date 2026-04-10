from __future__ import annotations

import importlib
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict

from .base import ModelOutput


_SYSTEM_PROMPT = """你是工程文档清洗器。目标是把输入文本做“低风险、保守”的降噪清洗，只输出干净文本。

严格约束：
- 宁可漏修，也不要猜测或改写事实。
- 禁止改动任何数字、单位、符号表达式。
- 允许的改动仅限：去除明显页眉页脚/页码、去除重复行、修复断行、多余空格、明显控制字符。
- 不要补全缺失内容，不要添加新信息。

输出格式必须是 json 对象：
{
  "cleaned_text": "string",
  "confidence": 0.0-1.0,
  "notes": "简短说明执行了哪些低风险清洗"
}
"""


def _require_httpx():
    try:
        return importlib.import_module("httpx")
    except ModuleNotFoundError as exc:
        raise RuntimeError("缺少可选依赖 httpx，启用模型清洗前请先安装它。") from exc


@dataclass(frozen=True)
class OpenAICompatClient:
    name: str
    base_url: str
    api_key_env: str
    model: str
    timeout_s: int = 60

    def clean_text(self, text: str) -> ModelOutput:
        api_key = os.environ.get(self.api_key_env, "") or self.api_key_env.strip()
        if not api_key:
            raise RuntimeError("Missing API key (set env var or put key in api_key_env).")

        payload: Dict[str, Any] = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        }
        headers = {"Authorization": f"Bearer {api_key}"}
        url = self.base_url.rstrip("/") + "/chat/completions"
        print(
            f"[REQ] name={self.name} model={self.model} base_url={self.base_url} "
            f"text_chars={len(text)} timeout_s={self.timeout_s} response_format=json_object"
        )
        httpx = _require_httpx()
        started = time.perf_counter()
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(url, json=payload, headers=headers)
            elapsed = time.perf_counter() - started
            print(
                f"[RESP] name={self.name} status={response.status_code} "
                f"elapsed_s={elapsed:.2f} body_chars={len(response.text)}"
            )
            response.raise_for_status()
            data = response.json()

        try:
            content = data["choices"][0]["message"]["content"]
        except Exception as exc:
            raise RuntimeError(f"Bad response shape from {self.name}") from exc

        try:
            parsed = json.loads(content)
        except Exception as exc:
            raise RuntimeError(f"Model {self.name} did not return valid JSON") from exc

        print(f"[PARSE] name={self.name} content_chars={len(content)} keys={sorted(parsed.keys())}")
        return ModelOutput(
            name=self.name,
            cleaned_text=str(parsed.get("cleaned_text", "")),
            confidence=float(parsed.get("confidence", 0.0)),
            notes=str(parsed.get("notes", "")),
        )
