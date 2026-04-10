# QAgent Prompt: engineering-doc-to-xiaogugit

当任务是“处理一份工程文档，并将结构化结果写入 xiaogugit 数据库”时，优先复用仓库现有 CLI，不要自创流程。

执行前必读：

1. 先读取 `README_CLI.md`，确认仓库可用 CLI。
2. 再读取 `tools/qagent_cli_prompts/README.md`，确认任务与工具映射。
3. 根据当前阶段，打开 `tools/qagent_cli_prompts/` 下对应说明文件，再执行命令。

阶段与工具说明映射：

- 预处理：`tools/qagent_cli_prompts/mm-denoise.md`
- 整体流水线：`tools/qagent_cli_prompts/pipeline.md`
- 实体抽取：`tools/qagent_cli_prompts/ner.md`
- 关系抽取：`tools/qagent_cli_prompts/entity-relation.md`
- 存储检索验证：`tools/qagent_cli_prompts/ontology-store.md`
- 规范实体检索：`tools/qagent_cli_prompts/ontology-core.md`
- 分类协商：`tools/qagent_cli_prompts/ontology-negotiator.md`
- 入库与版本写入：`tools/qagent_cli_prompts/xiaogugit.md`

固定执行要求：

- 不要只给建议，必须真正执行命令。
- 每个 CLI 首次调用前，先执行对应 `--help`。
- 优先使用 `python tools/cli_baseline.py run <cli> -- ...`，保持解释器与 `PYTHONPATH` 一致。
- 每完成一个阶段，输出一句简短进度。
- 遇到错误时，先检查 `returncode/stdout/stderr`，自行排查后继续。
- 除非缺少必须输入，否则不要停下来等人。
- 不要在未真实执行前，声称某个 CLI 因依赖问题不可用。
- 不要因为一次 `write` 失败就要求用户手动写库；应先排查 `project-id`、`filename`、`basevision`、`root-dir` 是否正确。
- `xiaogugit` 写入前，必须先做项目存在性检查和版本基线检查。

标准执行流程：

1. 预处理
   - 读取原始工程文档。
   - 优先查看 `tools/qagent_cli_prompts/mm-denoise.md`。
   - 先执行：
     ```bash
     python tools/cli_baseline.py run mm-denoise -- --help
     ```
   - 再按需要执行：
     ```bash
     python tools/cli_baseline.py run mm-denoise -- --config <config.yaml> --input <absolute_doc_path>
     ```
   - 目标：
     - 生成清洗后的纯文本文件
     - 生成对应 report JSON
   - 清洗要求：
     - 去除噪声、空行、乱码、重复标题、明显无效内容
     - 保留关键技术信息，不要擅自删减核心语义

2. 分层整理
   - 先查看 `tools/qagent_cli_prompts/ner.md`、`entity-relation.md`、`ontology-core.md`。
   - 分别先执行：
     ```bash
     python tools/cli_baseline.py run ner -- extract --help
     python tools/cli_baseline.py run entity-relation -- extract --help
     python tools/cli_baseline.py run ontology-core -- search --help
     ```
   - 必要时对清洗后文本执行实体与关系抽取。
   - 将文档整理为至少以下层次：
     - 项目背景/目标
     - 系统组件
     - 模块职责
     - 数据流或处理流程
     - 接口/命令/依赖
     - 风险点/待确认项
   - 原文没有的信息必须写“待确认”，不要编造。

3. 结构化产出
   - 优先查看 `tools/qagent_cli_prompts/pipeline.md`，确认是否已有现成结构化输出方式。
   - 先执行：
     ```bash
     python tools/cli_baseline.py run pipeline -- --help
     ```
   - 如果仓库已有适配格式，优先复用；否则生成字段稳定、可检索的 JSON 文件。
   - 建议结构至少包含：
     - `source_path`
     - `clean_text_path`
     - `document_title`
     - `project_background`
     - `system_components`
     - `module_responsibilities`
     - `data_flow`
     - `interfaces_commands_dependencies`
     - `risks_and_open_questions`
     - `evidence`
     - `generated_at`

4. 写入 xiaogugit
   - 先查看 `tools/qagent_cli_prompts/xiaogugit.md`。
   - 先执行：
     ```bash
     python tools/cli_baseline.py run xiaogugit -- --help
     python tools/cli_baseline.py run xiaogugit -- project list --help
     python tools/cli_baseline.py run xiaogugit -- write --help
     python tools/cli_baseline.py run xiaogugit -- read --help
     python tools/cli_baseline.py run xiaogugit -- version tree --help
     ```
   - 先确认 `--root-dir`、`project-id`、`filename`。
   - 先 `project list`，确认项目是否存在。
   - 如果项目不存在，先 `project init`。
   - 先 `read` 或 `version tree`，确认是否已有文件版本。
   - 根据版本树决定 `--basevision`；首次写入通常为 `0`，已有版本时使用当前版本号。
   - 只有完成上述检查后，才执行 `write`。
   - 写入示例：
     ```bash
     python tools/cli_baseline.py run xiaogugit -- --root-dir <storage_dir> write --project-id <project_id> --filename <filename> --message <message> --agent-name <agent_name> --committer-name <committer_name> --basevision 0 --data-file <structured_json_path>
     ```

5. 写入后验证
   - 写入后至少再执行一次读取或版本树命令验证：
     ```bash
     python tools/cli_baseline.py run xiaogugit -- --root-dir <storage_dir> read --project-id <project_id> --filename <filename>
     python tools/cli_baseline.py run xiaogugit -- --root-dir <storage_dir> version tree --project-id <project_id> --filename <filename>
     ```
   - 如有必要，再使用 `ontology-store` 或 `ontology-core` 做检索验证。

最终输出必须包含：

- 实际执行过的关键命令
- 是否入库成功
- 处理后的文本文件绝对路径
- 额外生成的结构化文件绝对路径
- 若有未解决问题，单独列出
- 若失败，必须包含失败发生在“依赖、项目初始化、版本基线、参数格式”中的哪一类，并附原始错误。

可直接复用的任务提示词模板：

```text
你现在就在 Ontology_Factory 项目根目录中工作，请直接执行，不要只给建议。

任务目标：
对我提供的一份工程文档做完整处理，流程包括：
1. 预处理
2. 分层整理
3. 产出结构化结果
4. 写入 xiaogugit 数据库
5. 最后把处理后的文本文件路径明确告诉我

执行要求：
1. 先读取 README_CLI.md，确认当前仓库内可用 CLI。
2. 再读取 tools/qagent_cli_prompts/README.md，确认任务与工具映射关系。
3. 涉及具体阶段时，必须先读取 tools/qagent_cli_prompts/ 下对应说明文件，再调用命令。
4. 优先使用当前项目里的 CLI 和现有工具，不要自己发明流程。
5. 必要时直接调用 terminal 工具执行命令，不要停留在口头说明。
6. 每完成一个阶段，输出简短进度。
7. 遇到错误先自行排查并继续，除非缺少必须输入。
8. 不要只返回分析，必须真正落盘、真正写库。
9. 所有最终输出默认使用中文。

工具说明位置：
- 预处理：tools/qagent_cli_prompts/mm-denoise.md
- 流水线：tools/qagent_cli_prompts/pipeline.md
- 实体抽取：tools/qagent_cli_prompts/ner.md
- 关系抽取：tools/qagent_cli_prompts/entity-relation.md
- 存储验证：tools/qagent_cli_prompts/ontology-store.md
- 规范实体检索：tools/qagent_cli_prompts/ontology-core.md
- 分类协商：tools/qagent_cli_prompts/ontology-negotiator.md
- 写入 xiaogugit：tools/qagent_cli_prompts/xiaogugit.md

处理流程要求：
一、预处理
- 读取原始工程文档
- 清洗无关噪声、空行、乱码、重复标题、明显无效内容
- 保留原始语义，不要随意删减关键技术信息
- 如有必要，生成标准化纯文本中间文件

二、分层
- 项目背景/目标
- 系统组件
- 模块职责
- 数据流或处理流程
- 接口/命令/依赖
- 风险点/待确认项
- 如果原文不完整，请明确标记“待确认”

三、结构化产出
- 生成适合入库的结构化结果
- 若仓库已有现成 CLI 或数据格式，优先遵循现有格式

四、写入数据库
- 使用 xiaogugit 相关 CLI 或现有仓库能力完成写入
- 如需先生成中间文件，再用 CLI 导入，也请直接完成
- 写入后请验证是否成功

最终输出要求：
1. 告诉我实际执行了哪些关键命令
2. 告诉我入库是否成功
3. 给出最终处理后的文本文件绝对路径
4. 如果生成了额外的结构化文件，也给出绝对路径
5. 如果有未解决问题，单独列出

待处理文档路径：
<把你的原始文档绝对路径填在这里>
```
