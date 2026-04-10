# QAgent Prompt: ontology-store

当任务是直接查询 SQLite 存储层中的页面、实体、关系或分类时，优先使用 `ontology-store` CLI。

## Agent 执行规则

- 调用前先确认数据库路径。
- 首次调用前先看帮助。
- 先明确 `--kind`，再构造查询。
- 要给别的步骤消费时，优先使用 `--stdout` 或落盘 `--output`。

## 首次必跑

```bash
python tools/cli_baseline.py run ontology-store -- query --help
```

## 常用命令模板

```bash
python tools/cli_baseline.py run ontology-store -- query --database <db> --kind pages --query <term> --stdout
python tools/cli_baseline.py run ontology-store -- query --database <db> --kind entities --query <term> --stdout
python tools/cli_baseline.py run ontology-store -- query --database <db> --kind relations --query <term> --stdout
python tools/cli_baseline.py run ontology-store -- query --database <db> --kind classifications --query <term> --stdout
python tools/cli_baseline.py run ontology-store -- query --database <db> --kind entities --query <term> --limit 20 --output <result.json> --stdout
```

## 参数选择规则

- `pages`：查原始 Wiki 页面或页面片段。
- `entities`：查规范实体。
- `relations`：查存储后的关系。
- `classifications`：查实体分类、本体标签。
- `--limit` 在结果可能很多时显式加上，避免输出过长。

## 输出怎么用

- 输出统一是 JSON，通常包含 `kind`、`count`、`items`。
- 重点看命中数量和前几条结果是否符合预期。
- 验证入库是否成功时，优先查 `entities`、`relations` 或 `classifications`。

## 失败排查

- `database` 路径错误时先检查是否指向 `.sqlite3`。
- 查不到结果时，先缩短 `query`，再去掉过强限定词。
- 命中过多时，加 `--limit` 并改用更具体关键词。

## 完成后汇报

- 数据库路径。
- 查询的 `kind` 与关键词。
- 命中数量。
- 最关键的前几条结果与 `stdout/stderr`。
