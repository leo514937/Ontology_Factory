# QAgent Prompt: mm-denoise

当任务是做文档预处理、清洗、降噪时，优先使用 `mm-denoise` CLI。

执行原则：

- 先确认 config 路径
- 单文件时优先传 `--input`
- 首次调用先阅读帮助

先执行：

```bash
python -m mm_denoise.cli --help
```

常用命令：

```bash
python -m mm_denoise.cli --config <config.yaml> --input <file>
python -m mm_denoise.cli --config <config.yaml> --base-dir <dir>
```

输出预期：

- 清洗后的文本文件
- 对应 report JSON
- stdout 中有处理状态

完成后应汇报：

- 输入文件或目录
- 产出的 clean text 路径
- report 路径
- 关键 stdout/stderr
