# QAgent Prompt: mm-denoise

当任务是做文档预处理、清洗、降噪时，优先使用 `mm-denoise` CLI。

## Agent 执行规则

- 首先确认配置文件路径。
- 单文件模式优先用 `--input`。
- 批量模式再用 `--base-dir`。
- 首次调用前先看帮助。
- 预处理结果通常会生成清洗文本和 report JSON，两者都要保留。

## 首次必跑

```bash
python tools/cli_baseline.py run mm-denoise -- --help
```

## 常用命令模板

```bash
python tools/cli_baseline.py run mm-denoise -- --config <config.yaml> --input <file>
python tools/cli_baseline.py run mm-denoise -- --config <config.yaml> --base-dir <dir>
```

## 参数选择规则

- `--config` 必填，指向预处理配置。
- 只处理一个工程文档时，用 `--input`。
- 批量扫描目录时，用 `--base-dir`。
- 输入优先传绝对路径，便于后续回报结果。

## 输出怎么用

- 产出通常包括清洗后的文本文件和对应 `.report.json`。
- 清洗文本用于 NER、关系抽取、结构化整理。
- report 用于说明清洗是否成功、是否做了保守降噪和具体输出路径。

## 失败排查

- 帮助命令若直接报缺依赖，例如 `bs4`，说明当前环境未装齐，先记录依赖缺失再决定是否继续。
- 输出为空时先检查原始文档是否能被 loader 正常读取。
- 清洗后文本过短时，先检查配置是否过强。

## 完成后汇报

- 输入文件或目录。
- 配置路径。
- 清洗文本绝对路径。
- report JSON 绝对路径。
- 关键 `stdout/stderr`。
