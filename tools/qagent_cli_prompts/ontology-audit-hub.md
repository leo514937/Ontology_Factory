# QAgent Prompt: ontology-audit-hub

当任务是运行审计主线、恢复人工中断的会话、做整体健康检查时，优先使用 `ontology_audit_hub.cli`。

执行原则：

- 首次调用先阅读帮助
- `run` 需要 YAML request 文件
- `resume` 需要 `session_id` 和响应文件
- `doctor` 适合先做环境检查

先执行：

```bash
python -m ontology_audit_hub.cli --help
python -m ontology_audit_hub.cli doctor
```

常用命令：

```bash
python -m ontology_audit_hub.cli run --request <request.yaml>
python -m ontology_audit_hub.cli resume --session-id <session> --response <response.yaml>
python -m ontology_audit_hub.cli doctor
python -m ontology_audit_hub.cli rebuild-lexical-index --collection <name>
```

输出预期：

- 审计结果 JSON
- 中断恢复结果 JSON
- readiness / doctor JSON

完成后应汇报：

- 运行的是 run、resume、doctor 还是 rebuild
- request / session_id / collection
- 关键结果
- 关键 stdout/stderr
