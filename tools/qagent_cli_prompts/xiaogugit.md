# QAgent Prompt: xiaogugit

当任务是做结构化数据的版本读写、日志、diff、回滚时，优先使用 `xiaogugit` CLI。

执行原则：

- 先确认 `--root-dir`
- 首次调用先阅读帮助
- 读操作优先于写操作

先执行：

```bash
python tools/cli_baseline.py run xiaogugit -- --help
python tools/cli_baseline.py run xiaogugit -- project list --help
```

常用命令：

```bash
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> project list
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> read --project-id <id> --filename <file>
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> write --project-id <id> --filename <file> --message <msg> --agent-name <agent> --committer-name <name> --basevision 0 --data-file <payload.json>
python tools/cli_baseline.py run xiaogugit -- --root-dir <storage> version tree --project-id <id> --filename <file>
```

输出预期：

- 统一 JSON

完成后应汇报：

- 使用的项目 ID 和文件名
- 是读、写、日志还是版本树
- 写操作时说明 message 和结果版本
- 关键 stdout/stderr
