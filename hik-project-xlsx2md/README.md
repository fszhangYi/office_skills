# hik-project-xlsx2md

Cursor Agent Skill：将立项/预研报告两列 XLSX 还原为 Markdown（`##` 分栏）。

与 [`hik-project-md2xlsx`](../hik-project-md2xlsx/) 配对。

## 安装位置

| 类型 | 路径 |
| --- | --- |
| 项目级 | `<工作区>/.cursor/skills/hik-project-xlsx2md/` |
| 个人级 | `~/.cursor/skills/hik-project-xlsx2md/` |

```bash
cp -a hik-project-xlsx2md /path/to/workspace/.cursor/skills/hik-project-xlsx2md
# 或
cp -a hik-project-xlsx2md ~/.cursor/skills/hik-project-xlsx2md
```

## 安装依赖

```bash
pip install openpyxl
```

## 命令行

```bash
python scripts/xlsx_to_md.py input.xlsx output.md
python scripts/xlsx_to_md.py "前盖具身智能上下料技术预研 v2.xlsx"   # → 同名 .md
```
