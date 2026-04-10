# QAgent Prompt: wikimg

当任务与 Wiki 页面浏览、搜索、展示、创建、更新相关时，优先使用 `wikimg`，不要先写新脚本。

执行原则：

- 先在 `D:\code\Ontology_Factory` 根目录下工作
- 首次调用前先看帮助
- 优先查询已有页面，再决定是否新建页面

先执行：

```bash
python tools/cli_baseline.py run wikimg -- --help
python tools/cli_baseline.py run wikimg -- list --help
```

常用命令：

```bash
python tools/cli_baseline.py run wikimg -- list
python tools/cli_baseline.py run wikimg -- search <query> --content
python tools/cli_baseline.py run wikimg -- show <layer:slug>
python tools/cli_baseline.py run wikimg -- new domain "<title>"
```

输出预期：

- 页面列表
- 匹配页面
- 页面正文
- 创建结果

完成后应汇报：

- 使用了哪个页面或 slug
- 是否找到已有页面
- 如果创建了页面，页面标题和层级是什么
- 关键 stdout/stderr
