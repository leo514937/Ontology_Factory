# QAgent Prompt: pipeline

当任务是整批或单文档运行 Ontology_Factory 主流程时，优先使用 `pipeline` CLI。

执行原则：

- 先确认输入是单文件还是目录
- 先确认 `preprocess` 配置路径
- 首次调用先阅读帮助
- 如果目标是 Wiki 主线，优先用 `--mode wiki`

先执行：

```bash
python -m pipeline.cli --help
```

常用命令：

```bash
python -m pipeline.cli --input <file> --mode wiki --preprocess-config <config.yaml>
python -m pipeline.cli --input-dir <dir> --mode wiki --glob "*.txt" --preprocess-config <config.yaml>
python -m pipeline.cli --input <file> --mode structured --preprocess-config <config.yaml>
```

输出预期：

- 运行结果 JSON
- 生成的 run/report/path 信息

完成后应汇报：

- 运行模式
- 输入范围
- 关键输出路径
- 关键 stdout/stderr
