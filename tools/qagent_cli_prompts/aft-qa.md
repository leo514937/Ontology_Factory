# QAgent Prompt: aft-qa

当任务是做问答、上传知识文档、重建 lexical index 或检查 QA 环境时，优先使用 `aft-qa` CLI。

执行原则：

- 首次调用先阅读帮助
- 问答优先使用 `--request-file`
- 上传知识时先确认文件路径和 collection
- 大多数情况下先跑 `doctor`

先执行：

```bash
python -m ontology_audit_hub.qa_cli --help
python -m ontology_audit_hub.qa_cli doctor
```

常用命令：

```bash
python -m ontology_audit_hub.qa_cli answer --request-file <request.json>
python -m ontology_audit_hub.qa_cli answer --question <question>
python -m ontology_audit_hub.qa_cli upload --file <doc>
python -m ontology_audit_hub.qa_cli rebuild-lexical-index --collection <name>
python -m ontology_audit_hub.qa_cli doctor
```

输出预期：

- QA response JSON
- upload metrics JSON
- doctor readiness JSON

完成后应汇报：

- 运行的是 answer、upload、rebuild-lexical-index 还是 doctor
- 输入文件或问题
- collection 或 session 信息
- 关键 stdout/stderr
