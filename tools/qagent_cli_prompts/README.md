# QAgent CLI Prompts

固定位置：`tools/qagent_cli_prompts/`

## 用途

- 给 agent 提供“看完就能直接调用 CLI”的任务提示词
- 每个 CLI 单独一份说明，减少试错
- 工程文档任务优先走一条快路径，而不是分散拼接命令

## 固定起手式

1. 先读 [`README_CLI.md`](D:/code/onto/Ontology_Factory/README_CLI.md)
2. 先执行 `python tools/cli_baseline.py doctor`
3. 再执行目标 CLI 的 `--help`
4. 最后执行真实命令

## 通用执行规则

- 优先使用 `python tools/cli_baseline.py run <cli> -- ...`
- 命令失败时先看 `returncode`、`stdout`、`stderr`
- 需要给后续程序继续消费时，优先使用 `--stdout` 或 JSON 文件输出
- 除非已经验证不适用，否则不要绕开仓库现有 CLI

## 提示词清单

- `wikimg.md`
- `mm-denoise.md`
- `pipeline.md`
- `engineering-doc-to-xiaogugit.md`
- `ner.md`
- `entity-relation.md`
- `ontology-store.md`
- `ontology-core.md`
- `ontology-negotiator.md`
- `xiaogugit.md`
- `ontology-audit-hub.md`
- `aft-review.md`
- `aft-qa.md`

## 任务映射

- Wiki 页面检索与管理：`wikimg.md`
- 文本清洗：`mm-denoise.md`
- 主流程编排：`pipeline.md`
- 工程文档入库：`engineering-doc-to-xiaogugit.md`
- 实体提取：`ner.md`
- 关系提取：`entity-relation.md`
- 存储查询：`ontology-store.md`
- 核心本体查询：`ontology-core.md`
- 本体协商：`ontology-negotiator.md`
- 版本化入库：`xiaogugit.md`

## 工程文档默认路径

当任务目标是“工程文档 -> 结构化 JSON -> xiaogugit”时，优先顺序固定为：

1. `README_CLI.md`
2. 本索引
3. `pipeline.md`
4. `engineering-doc-to-xiaogugit.md`

优先命令：

```bash
python tools/cli_baseline.py run pipeline -- --help
python tools/cli_baseline.py run pipeline -- --input <file> --mode engineering-doc
```

只有在 `engineering-doc` 模式经过实际验证后确认不适用时，才拆回 `mm-denoise / ner / entity-relation / ontology-core / ontology-store / xiaogugit` 分步执行。
