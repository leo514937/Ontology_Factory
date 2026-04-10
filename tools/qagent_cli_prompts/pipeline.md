# QAgent Prompt: pipeline

当任务是对单文档或目录运行 Ontology_Factory 主流程时，优先使用 `pipeline` CLI。

## Agent 执行规则

- 先判断输入是单文件还是目录。
- 先确认 `preprocess` 配置路径。
- 首次调用前先看帮助。
- 默认优先 `--mode wiki`，只有明确需要结构化链路时才用 `--mode structured`。
- 如果需要强制重跑，显式加 `--force-reingest`。

## 首次必跑

```bash
python tools/cli_baseline.py run pipeline -- --help
```

## 常用命令模板

```bash
python tools/cli_baseline.py run pipeline -- --input <file> --mode wiki --preprocess-config <config.yaml>
python tools/cli_baseline.py run pipeline -- --input <file> --mode structured --preprocess-config <config.yaml>
python tools/cli_baseline.py run pipeline -- --input-dir <dir> --mode wiki --glob "*.txt" --preprocess-config <config.yaml>
python tools/cli_baseline.py run pipeline -- --input <file> --mode wiki --preprocess-config <config.yaml> --pipeline-config <pipeline.yaml> --force-reingest
```

## 参数选择规则

- 处理单个文件时用 `--input`。
- 批量目录处理时用 `--input-dir` 与 `--glob`。
- 进入 Wiki 主线时用 `--mode wiki`。
- 只要结构化产物、不走 Wiki 主线时用 `--mode structured`。
- 配置不止一份时显式传 `--pipeline-config`。

## 输出怎么用

- 输出通常是运行结果 JSON。
- 重点关注 run id、report 路径、生成文件路径和处理状态。
- 如果任务目标是“真正落盘”，要记录这些输出路径。

## 失败排查

- 如果提示预处理配置缺失，先检查 `--preprocess-config`。
- 如果重复处理被跳过，但你确实要重跑，加 `--force-reingest`。
- 批量模式结果异常时，先拿一个样本文档切回单文件模式排查。

## 完成后汇报

- 运行模式。
- 输入范围。
- 配置文件路径。
- 关键输出路径与 `stdout/stderr`。
