# QAgent Prompt: ner

当任务是从文本中抽取实体时，优先使用 `ner` CLI，不要先实现新的抽取逻辑。

执行原则：

- 先确认输入文件路径
- 首次调用先阅读帮助
- 如果用户只关心某个主题，优先用 `--query`

先执行：

```bash
python tools/cli_baseline.py run ner -- extract --help
```

常用命令：

```bash
python tools/cli_baseline.py run ner -- extract --input <file> --stdout
python tools/cli_baseline.py run ner -- extract --input <file> --query <term> --max-sentences 4 --stdout
```

输出预期：

- `NerDocument` JSON

完成后应汇报：

- 文档 ID
- 抽取出的关键实体
- 如果用了 `--query`，说明筛选条件
- 关键 stdout/stderr
