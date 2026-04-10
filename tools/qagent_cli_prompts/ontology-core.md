# QAgent Prompt: ontology-core

当任务是做规范实体检索、canonical search、查看 mentions 或 relations 时，优先使用 `ontology-core` CLI。

执行原则：

- 先确认数据库路径
- 首次调用先阅读帮助
- 默认先做普通 search，只有需要时再加 `--include-mentions` 或 `--include-relations`

先执行：

```bash
python tools/cli_baseline.py run ontology-core -- search --help
```

常用命令：

```bash
python tools/cli_baseline.py run ontology-core -- search --database <db> --query <term> --stdout
python tools/cli_baseline.py run ontology-core -- search --database <db> --query <term> --include-mentions --include-relations --stdout
```

输出预期：

- 统一 JSON，包含 `query`、`count`、`items`

完成后应汇报：

- 查询词
- 命中的 canonical entities
- 是否附带 mentions / relations
- 关键 stdout/stderr
