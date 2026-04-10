# QAgent Prompt: entity-relation

当任务是从文本中抽取实体关系时，优先使用 `entity-relation` CLI，不要自己拼接新的关系抽取脚本。

## Agent 执行规则

- 输入优先使用清洗后的纯文本。
- 首次调用前先看帮助。
- 需要落盘时用 `--output`，需要即时消费时加 `--stdout`。
- 如果任务只聚焦某个主题，可先用 `--query` 缩小范围。

## 首次必跑

```bash
python tools/cli_baseline.py run entity-relation -- extract --help
```

## 常用命令模板

```bash
python tools/cli_baseline.py run entity-relation -- extract --input <file> --stdout
python tools/cli_baseline.py run entity-relation -- extract --input <file> --output <result.json> --stdout
python tools/cli_baseline.py run entity-relation -- extract --input <file> --doc-id <doc_id> --stdout
python tools/cli_baseline.py run entity-relation -- extract --input <file> --query <term> --max-sentences 6 --stdout
```

## 参数选择规则

- `--input` 必填。
- `--doc-id` 用于后续和实体结果、结构化文件做关联。
- `--query` 适合只关心一个概念、模块或系统时使用。
- `--max-sentences` 一般控制在 `4-8` 之间，避免噪声太多。

## 输出怎么用

- 输出是 `RelationDocument` JSON。
- 重点关注关系数量、关系两端实体、关系类型、证据句。
- 分层整理时，可据此生成“模块职责”“数据流”“依赖关系”部分。

## 失败排查

- 结果为空时，先去掉 `--query`。
- 如果关系很多但无效，缩小 `--query` 并降低上下文句子数量。
- 如果输入文本包含严重换行噪声，先回到 `mm-denoise` 重新预处理。

## 完成后汇报

- 输入文件路径。
- 是否用了 `--query`。
- 关键关系有哪些。
- 结果文件路径与关键 `stdout/stderr`。
