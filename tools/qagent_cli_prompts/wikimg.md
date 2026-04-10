# QAgent Prompt: wikimg

当任务涉及 Wiki 页面浏览、检索、展示、创建、改名、移动、删除或体检时，优先使用 `wikimg` CLI，不要先写新脚本。

## Agent 执行规则

- 工作目录默认设为仓库根目录 `D:\code\onto\Ontology_Factory`。
- 首次调用前先执行帮助命令，确认当前子命令是否可用。
- 优先查询已有页面，再决定是否新建页面。
- 需要结构化结果时优先加 `--json`。

## 首次必跑

```bash
python tools/cli_baseline.py run wikimg -- --help
python tools/cli_baseline.py run wikimg -- list --help
python tools/cli_baseline.py run wikimg -- search --help
```

## 常用命令模板

```bash
python tools/cli_baseline.py run wikimg -- --root <workspace> list --json
python tools/cli_baseline.py run wikimg -- --root <workspace> search <query> --content --json
python tools/cli_baseline.py run wikimg -- --root <workspace> show <layer:slug>
python tools/cli_baseline.py run wikimg -- --root <workspace> new domain "<title>"
python tools/cli_baseline.py run wikimg -- --root <workspace> doctor --json
```

## 参数选择规则

- 不确定工作区时，显式传 `--root <workspace>`。
- 只想看页面标题或 slug，用 `list`。
- 需要全文匹配时，用 `search <query> --content`。
- 已有 `layer:slug` 时直接 `show`，不要先盲搜。
- 新建页面前先跑一次 `search`，避免重复建页。

## 输出怎么用

- `list`：用于确认当前有哪些页面与 slug。
- `search`：用于确认是否已有相关页面、哪些页面最接近。
- `show`：用于读取页面正文和已有结构。
- `doctor`：用于检查 Wiki 工作区结构是否健康。

## 失败排查

- `returncode != 0` 时，先看 `stderr` 是否是 `--root` 不正确。
- 搜不到页面时，先缩短关键词，再去掉 `--content` 试一次。
- 新建失败时，先确认标题是否和已有页面冲突。

## 完成后汇报

- 使用了哪个子命令。
- 工作区根目录是什么。
- 命中的页面标题、slug 或创建结果。
- 关键 `stdout/stderr`。
