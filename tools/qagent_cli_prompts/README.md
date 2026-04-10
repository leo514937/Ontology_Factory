# QAgent CLI Prompts

固定位置：`tools/qagent_cli_prompts/`

## 用途

- 给 agent 提供“看完就能直接调用 CLI”的任务提示词。
- 每个 CLI 单独一份说明文件，减少 agent 自己猜流程。
- 建议顺序是：先读本索引，再读对应 CLI 提示词，再执行命令。

## 通用执行规范

- 默认在仓库根目录 `D:\code\onto\Ontology_Factory` 下工作。
- 先读 [`README_CLI.md`](D:/code/onto/Ontology_Factory/README_CLI.md) 确认可用 CLI。
- 能用 `python tools/cli_baseline.py run <cli> -- ...` 的场景，优先用它，保证解释器和 `PYTHONPATH` 一致。
- 每个 CLI 第一次调用前，先执行对应 `--help`。
- 命令失败时，优先记录 `returncode`、`stdout`、`stderr`，不要直接改流程。
- 需要程序继续消费时，优先使用 JSON 输出、`--stdout` 或显式 `--output`。
- 不要在没有真实复现的情况下，声称某个 CLI 缺依赖或无法运行。
- 如果是参数缺失、项目未初始化或版本基线不匹配，应继续补齐步骤，不要把任务退回给用户手动执行。

## 提示词清单

- `wikimg.md`
- `ner.md`
- `entity-relation.md`
- `ontology-store.md`
- `ontology-core.md`
- `ontology-negotiator.md`
- `pipeline.md`
- `mm-denoise.md`
- `xiaogugit.md`
- `engineering-doc-to-xiaogugit.md`
- `ontology-audit-hub.md`
- `aft-review.md`
- `aft-qa.md`

## 任务与提示词映射

- Wiki 页面浏览、检索、建页：`wikimg.md`
- 实体抽取：`ner.md`
- 关系抽取：`entity-relation.md`
- 库内原始存储检索：`ontology-store.md`
- 规范实体检索：`ontology-core.md`
- 本体协商与分类：`ontology-negotiator.md`
- 单文档/目录主流程运行：`pipeline.md`
- 文档预处理与清洗：`mm-denoise.md`
- 结构化版本读写与回滚：`xiaogugit.md`
- 工程文档清洗、分层、结构化并写入 xiaogugit：`engineering-doc-to-xiaogugit.md`
- 审计主线、恢复、体检：`ontology-audit-hub.md`
- GitHub 审查：`aft-review.md`
- QA 与知识上传维护：`aft-qa.md`

## 推荐选择顺序

- 先做预处理：`mm-denoise.md`
- 再做抽取：`ner.md`、`entity-relation.md`
- 再做检索验证：`ontology-store.md`、`ontology-core.md`
- 再决定是否跑主流程：`pipeline.md`
- 需要版本化入库时：`xiaogugit.md`
