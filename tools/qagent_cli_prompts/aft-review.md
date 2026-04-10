# QAgent Prompt: aft-review

当任务是对 GitHub 仓库做自动审查，或检查 review 运行环境是否就绪时，优先使用 `aft-review` CLI。

## Agent 执行规则

- 优先使用 `python tools/cli_baseline.py run aft-review -- ...`。
- 首次调用前先看帮助并跑一次 `doctor`。
- 有完整请求文件时，优先 `--request-file`。
- 只有没有请求文件时，才使用直接参数模式。

## 首次必跑

```bash
python tools/cli_baseline.py run aft-review -- --help
python tools/cli_baseline.py run aft-review -- doctor
```

## 常用命令模板

```bash
python tools/cli_baseline.py run aft-review -- github --request-file <request.json>
python tools/cli_baseline.py run aft-review -- github --repository-url <url> --ref <ref> --path <path>
python tools/cli_baseline.py run aft-review -- github --repository-url <url> --ref <ref> --path <path1> --path <path2>
python tools/cli_baseline.py run aft-review -- doctor
```

## 参数选择规则

- `--request-file`：最稳妥，适合自动化。
- 直传模式至少需要 `--repository-url`、`--ref` 和一个 `--path`。
- 要限定审查范围时，可重复传多个 `--path`。

## 输出怎么用

- `github` 输出 review report JSON。
- `doctor` 输出 readiness JSON。
- 如果 `doctor.ready=false`，要先报告环境问题，不要假装已完成审查。

## 失败排查

- 直传模式缺参数时会直接失败，先补齐仓库 URL、ref 和 path。
- `doctor` 不 ready 时，先看 LLM 配置与运行时设置。
- 请求文件模式失败时，先检查 JSON 字段。

## 完成后汇报

- 使用的是请求文件模式还是直接参数模式。
- 仓库 URL、ref、path 范围。
- `doctor` 是否 ready。
- 关键 `stdout/stderr`。
