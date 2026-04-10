# QAgent Prompt: entity-relation

当任务是从文本中抽取关系时，优先使用 `entity-relation` CLI，不要先写新的关系抽取脚本。

执行原则：

- 先确认输入文件路径
- 首次调用先阅读帮助
- 如果用户只关心某个主题，优先用 `--query`

先执行：

```bash
python tools/cli_baseline.py run entity-relation -- extract --help
```

常用命令：

```bash
python tools/cli_baseline.py run entity-relation -- extract --input <file> --stdout
python tools/cli_baseline.py run entity-relation -- extract --input <file> --query <term> --max-sentences 6 --stdout
```

输出预期：

- `RelationDocument` JSON

完成后应汇报：

- 关系数量
- 关键关系对
- 如果用了 `--query`，说明筛选条件
- 关键 stdout/stderr
