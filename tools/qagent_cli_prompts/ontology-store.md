# QAgent Prompt: ontology-store

当任务是直接查询 SQLite 存储层中的页面、实体、关系或分类时，优先使用 `ontology-store` CLI。

执行原则：

- 先确认数据库路径
- 首次调用先阅读帮助
- 先明确 `--kind` 是 `pages`、`entities`、`relations` 还是 `classifications`

先执行：

```bash
python tools/cli_baseline.py run ontology-store -- query --help
```

常用命令：

```bash
python tools/cli_baseline.py run ontology-store -- query --database <db> --kind pages --query <term> --stdout
python tools/cli_baseline.py run ontology-store -- query --database <db> --kind entities --query <term> --stdout
python tools/cli_baseline.py run ontology-store -- query --database <db> --kind relations --query <term> --stdout
python tools/cli_baseline.py run ontology-store -- query --database <db> --kind classifications --query <term> --stdout
```

输出预期：

- 统一 JSON，包含 `kind`、`count`、`items`

完成后应汇报：

- 查询类型
- 命中数量
- 最关键的前几条结果
- 关键 stdout/stderr
