# QAgent Prompt: xiaogugit

当任务是做结构化 JSON 的项目初始化、读取、写入、历史查看、版本树检查、差异比较、回滚或删除时，优先使用 `xiaogugit` CLI。

## Agent 执行规则

- 优先使用 `python tools/cli_baseline.py run xiaogugit -- ...`。
- 调用前先确认 `--root-dir`。
- 第一次使用时先看总帮助，再看具体子命令帮助。
- 写入前优先先读当前版本，避免盲写。
- 需要稳定落库时，结构化数据优先写入 JSON 文件，再通过 `--data-file` 导入。
- 不要仅凭猜测声称“缺少依赖”或“当前环境不能运行”。必须先真实执行命令并记录实际报错。
- 如果只是参数不满足，不算环境不可用；应继续补齐 `project-id`、`filename`、`basevision` 等参数并重试。
- 除非真实执行后确认 CLI 完全不可运行，否则不要让用户“手动写库”代替 agent 执行。
- 遇到失败时，优先区分三类问题：环境依赖问题、项目不存在、参数不完整。

## 首次必跑

```bash
python tools/cli_baseline.py run xiaogugit -- --help
python tools/cli_baseline.py run xiaogugit -- project list
python tools/cli_baseline.py run xiaogugit -- write --help
python tools/cli_baseline.py run xiaogugit -- read --help
python tools/cli_baseline.py run xiaogugit -- version tree --help
```

## 常用命令模板

```bash
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> project init --project-id <id> --name <name> --description <desc>
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> project list
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> file list --project-id <id>
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> read --project-id <id> --filename <file>
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> log --project-id <id>
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> write --project-id <id> --filename <file> --message <msg> --agent-name <agent> --committer-name <name> --basevision 0 --data-file <payload.json>
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> version tree --project-id <id> --filename <file>
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> diff versions --project-id <id> --base-version-id <base> --target-version-id <target> --filename <file>
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> rollback version --project-id <id> --version-id <version_id> --filename <file>
```

## 标准入库顺序

```bash
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> project list
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> project init --project-id <id> --name <name>
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> read --project-id <id> --filename <file>
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> version tree --project-id <id> --filename <file>
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> write --project-id <id> --filename <file> --message <msg> --agent-name <agent> --committer-name <name> --basevision <n> --data-file <payload.json>
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> read --project-id <id> --filename <file>
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> version tree --project-id <id> --filename <file>
```

## 参数选择规则

- `project init`：项目不存在时先初始化。
- `read`：写入前确认当前数据。
- `write`：写 JSON 并创建新版本。
- `--basevision`：写入时必填，通常先通过 `read`/`version tree` 确认当前版本号。
- 首次写入新文件时，`--basevision` 通常为 `0`。
- 不是首次写入时，`--basevision` 必须与现有版本树匹配，不能随便写 `0`。
- `log`：查看提交历史。
- `version tree`：确认版本链是否正常。
- `diff versions`：比较两个版本。
- `rollback version`：按版本回退。

## 输出怎么用

- 所有输出统一为 JSON。
- 写入成功后要记录项目 ID、文件名、版本信息、提交信息。
- 验证写库成功时，至少再执行一次 `read` 或 `version tree`。

## 失败排查

- 项目不存在时先跑 `project init` 或核对 `project-id`。
- 写入失败时先检查 `payload.json` 是否是合法 JSON。
- 版本冲突或基线不对时，先看 `version tree` 和 `log`。
- `--root-dir` 不对时会读不到项目，先确认实际存储目录。
- 若报 `No module named 'git'` 或 `No module named 'gitpython'`，先把完整报错原文记录下来，再判断是否真是环境缺依赖。
- 若 `--help` 可以执行成功，则不要再声称该 CLI 因依赖问题无法运行；应继续排查参数或项目状态。
- 若 `write` 报参数缺失，先补齐 `--project-id`、`--filename`、`--message`、`--agent-name`、`--committer-name`、`--basevision`、`--data-file/--data-json`。
- 若 `read` 报文件不存在，不代表不能写库；先确认是否是“首次写入”场景，再走 `project init + write`。

## 完成后汇报

- `root-dir`、`project-id`、`filename`。
- 跑的是读、写、日志、版本树、diff 还是回滚。
- 写入时的 `message`、`basevision` 和返回结果。
- 验证命令及关键 `stdout/stderr`。
- 如果失败，必须附上真实执行命令和原始错误，不要只给笼统结论。
