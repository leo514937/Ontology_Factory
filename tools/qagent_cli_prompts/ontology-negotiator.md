# QAgent Prompt: ontology-negotiator

当任务是对图或节点做本体协商、分类推断时，优先使用 `ontology-negotiator` CLI。

执行原则：

- 先确认图文件路径和配置文件路径
- 首次调用先阅读帮助
- 如果用户只关心单个节点，优先加 `--node-id`

先执行：

```bash
python tools/cli_baseline.py run ontology-negotiator -- classify --help
```

常用命令：

```bash
python tools/cli_baseline.py run ontology-negotiator -- classify --graph <graph.json> --config <config.toml> --stdout
python tools/cli_baseline.py run ontology-negotiator -- classify --graph <graph.json> --node-id <node> --config <config.toml> --stdout
```

输出预期：

- 图模式：`{"mode":"graph","results":[...]}`
- 单节点模式：`{"mode":"node","result":{...}}`

完成后应汇报：

- 运行模式
- 节点或图范围
- 关键分类结果
- 关键 stdout/stderr
