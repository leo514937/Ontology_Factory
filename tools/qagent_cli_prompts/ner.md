# QAgent Prompt: ner

当任务是从纯文本中抽取实体时，优先使用 `ner` CLI，不要自行实现新的抽取逻辑。

## Agent 执行规则

- 输入应优先使用清洗后的纯文本文件。
- 首次调用前先看帮助。
- 需要给下游程序消费时，优先同时使用 `--output` 和 `--stdout`。
- 如果用户只关心某个主题，优先加 `--query` 限定范围。

## 首次必跑

```bash
python tools/cli_baseline.py run ner -- extract --help
```

## 常用命令模板

```bash
python tools/cli_baseline.py run ner -- extract --input <file> --stdout
python tools/cli_baseline.py run ner -- extract --input <file> --output <result.json> --stdout
python tools/cli_baseline.py run ner -- extract --input <file> --doc-id <doc_id> --stdout
python tools/cli_baseline.py run ner -- extract --input <file> --query <term> --max-sentences 4 --stdout
```

## 参数选择规则

- `--input` 必填，必须指向纯文本文件。
- `--output` 用于落盘结果，适合后续再处理。
- `--doc-id` 用于稳定标识文档，避免默认文件名不清晰。
- `--query` 只在“聚焦某一主题”时使用。
- `--max-sentences` 只在配合 `--query` 时使用，避免截太宽。

## 输出怎么用

- 输出是 `NerDocument` JSON。
- 重点关注文档 ID、实体列表、实体类型、命中片段。
- 如果要做结构化入库，保留原始 JSON，不要只摘抄自然语言。

## 失败排查

- 输入不存在时先检查路径是否为绝对路径。
- 输出为空时，先去掉 `--query` 跑全量，再看文本是否过度清洗。
- 如果 `stderr` 提到模型或网络问题，先记录，再退回不带额外模型参数的默认模式。

## 完成后汇报

- 输入文件路径。
- 是否用了 `--query`。
- 关键实体有哪些。
- 结果文件路径与关键 `stdout/stderr`。
