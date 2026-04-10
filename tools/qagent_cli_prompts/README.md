# QAgent CLI Prompts

固定位置：`tools/qagent_cli_prompts/`

用途：

- 给 QAgent 提供一组可直接读取的 CLI 提示词
- 每个 CLI 一份独立提示词，便于按需打开
- 约定 QAgent 先看本索引，再按任务打开对应文件

使用建议：

- 先在仓库根目录 `D:\code\Ontology_Factory` 下工作
- 首次使用某个 CLI 前，先执行该 CLI 的 `--help`
- 如果需要统一环境基线，优先参考 `tools/cli_baseline.py`
- 如果命令失败，先总结 `returncode/stdout/stderr`，再决定是否改代码

可用提示词：

- `wikimg.md`
- `ner.md`
- `entity-relation.md`
- `ontology-store.md`
- `ontology-core.md`
- `ontology-negotiator.md`
- `pipeline.md`
- `mm-denoise.md`
- `xiaogugit.md`
- `ontology-audit-hub.md`
- `aft-review.md`
- `aft-qa.md`

任务到 CLI 的推荐映射：

- Wiki 页面管理、页面搜索、页面创建：`wikimg.md`
- 实体抽取：`ner.md`
- 关系抽取：`entity-relation.md`
- 存储层检索：`ontology-store.md`
- 规范实体检索：`ontology-core.md`
- 本体协商与分类：`ontology-negotiator.md`
- 整体流水线运行：`pipeline.md`
- 文本预处理与清洗：`mm-denoise.md`
- 结构化版本存储读写：`xiaogugit.md`
- 审计主线与恢复：`ontology-audit-hub.md`
- GitHub 审查：`aft-review.md`
- QA 与知识库维护：`aft-qa.md`
