# QAgent Prompt: ontology-audit-hub

当任务是运行审计主线、恢复人工中断会话、做整体环境体检或重建 lexical index 时，优先使用 `ontology_audit_hub.cli`。

## Agent 执行规则

- 该 CLI 不在 `tools/cli_baseline.py` 的快捷封装里时，可以直接用 `python -m ontology_audit_hub.cli ...`。
- 首次调用前先执行帮助或 `doctor`。
- `run` 需要 YAML request 文件。
- `resume` 需要 `session_id` 和人工响应 YAML。
- 环境不确定时先跑 `doctor`。

## 首次必跑

```bash
python -m ontology_audit_hub.cli --help
python -m ontology_audit_hub.cli doctor
```

## 常用命令模板

```bash
python -m ontology_audit_hub.cli run --request <request.yaml>
python -m ontology_audit_hub.cli resume --session-id <session_id> --response <response.yaml>
python -m ontology_audit_hub.cli doctor
python -m ontology_audit_hub.cli rebuild-lexical-index --collection <name>
```

## 参数选择规则

- 有完整请求文件时优先 `run --request`。
- 人工中断后继续流程时用 `resume`。
- 只做环境体检时用 `doctor`。
- 只补词法索引时用 `rebuild-lexical-index`。

## 输出怎么用

- `run`：返回审计结果 JSON 或人工中断载荷。
- `resume`：返回恢复后的结果 JSON。
- `doctor`：返回 readiness JSON。
- `rebuild-lexical-index`：返回 collection、批次数和 chunk 数。

## 失败排查

- `doctor` 不 ready 时，先不要继续主流程。
- `run`/`resume` 报 YAML 问题时，先检查请求文件编码和字段。
- 重建索引报错时，先检查 Qdrant 和 lexical db 配置。

## 完成后汇报

- 跑的是 `run`、`resume`、`doctor` 还是 `rebuild-lexical-index`。
- request/session/collection 关键信息。
- readiness 或关键结果。
- 关键 `stdout/stderr`。
