# QAgent Prompt: aft-review

当任务是对 GitHub 仓库做审查或检查 review 环境就绪状态时，优先使用 `aft-review` CLI。

执行原则：

- 首次调用先阅读帮助
- 如果有完整请求文件，优先用 `--request-file`
- 只有在没有请求文件时，才用直接参数模式

先执行：

```bash
python -m ontology_audit_hub.review_cli --help
python -m ontology_audit_hub.review_cli doctor
```

常用命令：

```bash
python -m ontology_audit_hub.review_cli github --request-file <request.json>
python -m ontology_audit_hub.review_cli github --repository-url <url> --ref <ref> --path <path>
python -m ontology_audit_hub.review_cli doctor
```

输出预期：

- review report JSON
- doctor readiness JSON

完成后应汇报：

- 请求模式是文件还是直传参数
- 仓库 URL、ref、path 范围
- doctor 是否 ready
- 关键 stdout/stderr
