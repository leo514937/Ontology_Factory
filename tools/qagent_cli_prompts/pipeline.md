# QAgent Prompt: pipeline

当任务需要执行 Ontology_Factory 主流程时，优先使用 `pipeline` CLI。

## 先做什么

1. 先执行：

```bash
python tools/cli_baseline.py doctor --cli pipeline
python tools/cli_baseline.py run pipeline -- --help
```

2. 再判断是以下哪一种模式：

- `wiki`
- `structured`
- `engineering-doc`

## 工程文档任务默认模式

如果输入是一份工程文本，目标是清洗、抽取、结构化并写入 `xiaogugit`，默认优先：

```bash
python tools/cli_baseline.py run pipeline -- --input <file> --mode engineering-doc
```

可选参数：

- `--project-id`
- `--filename`
- `--xiaogugit-root`
- `--document-title`
- `--preprocess-config`
- `--pipeline-config`

## 其他常用模板

```bash
python tools/cli_baseline.py run pipeline -- --input <file> --mode wiki --preprocess-config <config.yaml>
python tools/cli_baseline.py run pipeline -- --input <file> --mode structured --preprocess-config <config.yaml>
python tools/cli_baseline.py run pipeline -- --input-dir <dir> --mode wiki --glob "*.txt" --preprocess-config <config.yaml>
python tools/cli_baseline.py run pipeline -- --input <file> --mode wiki --preprocess-config <config.yaml> --pipeline-config <pipeline.yaml> --force-reingest
```

## 选择规则

- 单文件处理用 `--input`
- 目录批处理用 `--input-dir` 配合 `--glob`
- 需要写 Wiki 用 `--mode wiki`
- 只要结构化结果用 `--mode structured`
- 工程文档入库用 `--mode engineering-doc`

## 结果关注点

- `run_id`
- `report_path`
- 产物路径
- 是否完成写入与验证

## 失败排查

- 先看 `doctor` 输出
- 再看 `--help`
- 再看 `returncode/stdout/stderr`
- `engineering-doc` 模式失败时，优先检查 `preprocess` 配置、`xiaogugit` root、项目基线和输入文件路径
