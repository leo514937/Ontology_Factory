# QAgent Prompt: aft-qa

当任务是做问答、上传知识文档、重建 lexical index 或检查 QA 运行环境时，优先使用 `aft-qa` CLI。

## Agent 执行规则

- 优先使用 `python tools/cli_baseline.py run aft-qa -- ...`。
- 首次调用前先看帮助并跑一次 `doctor`。
- 问答优先使用 `--request-file`，只有临时单问时才走 `--question`。
- 上传知识前先确认文件路径和 collection。

## 首次必跑

```bash
python tools/cli_baseline.py run aft-qa -- --help
python tools/cli_baseline.py run aft-qa -- doctor
```

## 常用命令模板

```bash
python tools/cli_baseline.py run aft-qa -- answer --request-file <request.json>
python tools/cli_baseline.py run aft-qa -- answer --question "<question>" --session-id <session_id>
python tools/cli_baseline.py run aft-qa -- upload --file <doc> --collection <name>
python tools/cli_baseline.py run aft-qa -- rebuild-lexical-index --collection <name>
python tools/cli_baseline.py run aft-qa -- doctor
```

## 参数选择规则

- `answer --request-file`：适合自动化和复杂问题。
- `answer --question`：适合临时问答；建议补 `--session-id`。
- `upload --file`：上传知识文档时必填。
- `--collection`：不确定默认 collection 时显式传。

## 输出怎么用

- `answer`：返回 QA response JSON。
- `upload`：返回上传指标、chunk 或 collection 信息。
- `rebuild-lexical-index`：返回回填统计。
- `doctor`：返回 QA、RAG、graph、lexical index 的 readiness。

## 失败排查

- `doctor` 不 ready 时，先停在环境排查。
- `answer` 直传模式未带 `--question` 会失败。
- `upload` 失败时，先检查文件是否存在、collection 是否正确。

## 完成后汇报

- 跑的是 `answer`、`upload`、`rebuild-lexical-index` 还是 `doctor`。
- 输入问题、文件路径或 collection。
- session 信息。
- 关键 `stdout/stderr`。
