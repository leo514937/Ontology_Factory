# QAgent Prompt: ontology-core

当任务是做规范实体检索、canonical search、补充 mentions 或 relations 时，优先使用 `ontology-core` CLI。

## Agent 执行规则

- 先确认数据库路径。
- 首次调用前先看帮助。
- 默认先做最小搜索，只在必要时加 `--include-mentions` 或 `--include-relations`。
- 需要机器可消费结果时，优先加 `--stdout`。

## 首次必跑

```bash
python tools/cli_baseline.py run ontology-core -- search --help
```

## 常用命令模板

```bash
python tools/cli_baseline.py run ontology-core -- search --database <db> --query <term> --stdout
python tools/cli_baseline.py run ontology-core -- search --database <db> --query <term> --limit 10 --stdout
python tools/cli_baseline.py run ontology-core -- search --database <db> --query <term> --include-mentions --stdout
python tools/cli_baseline.py run ontology-core -- search --database <db> --query <term> --include-mentions --include-relations --output <result.json> --stdout
```

## 参数选择规则

- 只想知道是否有规范实体：基础 `search` 即可。
- 需要核对文本中具体提及方式：加 `--include-mentions`。
- 需要看邻接关系：再加 `--include-relations`。
- 结果很多时，加 `--limit`。

## 输出怎么用

- 输出通常包含 `query`、`count`、`items`。
- 看 `items` 里的 canonical entity、当前分类和可选的 mentions/relations。
- 适合用来验证“这个概念是否已经被库里规范化”。

## 失败排查

- 无结果时，先缩短关键词或换同义词。
- 输出过大时，去掉 `--include-*` 并加 `--limit`。
- 如果库里明明有但查不到，回头用 `ontology-store` 查原始数据层。

## 完成后汇报

- 数据库路径。
- 查询词。
- 是否附带 mentions / relations。
- 命中的 canonical entities 与关键 `stdout/stderr`。
