# QAgent Unified Config

Fixed files:
- `config/qagent.local.example.toml`
- `config/qagent.local.toml`

This config is the single local source of truth for Ontology_Factory CLI LLM calls.
When the file is present and `[llm]` is configured, the repository will route the
same `base_url`, `api_key`, and `model` into:
- `ner`
- `pipeline`
- `ontology-negotiator`
- `mm-denoise`
- `aft-review`
- `aft-qa`

Notes:
- `config/qagent.local.toml` is gitignored.
- Keep real secrets only in `config/qagent.local.toml`.
- CLI flags can still override local values when a command explicitly passes them.

Fields:
- `[llm].enabled`: master switch for unified LLM injection
- `[llm].base_url`: shared OpenAI-compatible base URL
- `[llm].api_key`: shared API key
- `[llm].model`: shared model name
- `[llm].timeout_s`: shared timeout default

Recommended usage:
1. Copy `config/qagent.local.example.toml` to `config/qagent.local.toml`.
2. Fill in your real `base_url`, `api_key`, and `model`.
3. Run CLIs through `tools/cli_baseline.py` when possible so the shared
   environment is applied consistently across Windows and macOS.
