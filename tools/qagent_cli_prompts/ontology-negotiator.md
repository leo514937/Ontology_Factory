# QAgent Prompt: ontology-negotiator

当任务是对图或节点做本体协商、分类推断时，优先使用 `ontology-negotiator` CLI。

## Agent 执行规则

- 先确认图文件路径。
- 如有配置文件，优先显式传 `--config`。
- 首次调用前先看帮助。
- 只关心单个节点时，优先使用 `--node-id`。

## 首次必跑

```bash
python tools/cli_baseline.py run ontology-negotiator -- classify --help
```

## 常用命令模板

```bash
python tools/cli_baseline.py run ontology-negotiator -- classify --graph <graph.json> --config <config.toml> --stdout
python tools/cli_baseline.py run ontology-negotiator -- classify --graph <graph.json> --node-id <node_id> --config <config.toml> --stdout
python tools/cli_baseline.py run ontology-negotiator -- classify --graph <graph.json> --config <config.toml> --artifact-root <artifact_dir> --output <result.json> --stdout
```

## 参数选择规则

- `--graph` 必填，指向 GraphInput JSON。
- `--config` 没有明确要求也建议带上，保持结果一致。
- `--node-id` 用于单节点分类，适合排查局部问题。
- `--artifact-root` 用于保留中间产物，适合调试。
- `--output` 用于落盘完整分类结果。

## 输出怎么用

- 图模式输出形如 `{"mode":"graph","results":[...]}`。
- 节点模式输出形如 `{"mode":"node","result":{...}}`。
- 关注分类标签、置信信息、失败节点和中间证据。

## 失败排查

- 如果 `stderr` 只有第三方告警、`returncode=0`，可视为成功但要简要记录。
- 图文件报错时先检查 JSON 是否完整。
- 结果异常时，改用 `--node-id` 缩小范围。

## 完成后汇报

- 运行模式是图级还是节点级。
- 输入图路径、节点 ID 或 artifact 目录。
- 关键分类结果。
- 关键 `stdout/stderr`。
