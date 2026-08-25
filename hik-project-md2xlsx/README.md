# hik-project-md2xlsx

Cursor Agent Skill：将立项/预研 Markdown 导出为立项报告风格两列 XLSX（微软雅黑、行高自适应、GFM 表→编号列表）。

与 [`hik-project-xlsx2md`](../hik-project-xlsx2md/) 配对。

## 安装位置

| 类型 | 路径 |
| --- | --- |
| 项目级 | `<工作区>/.cursor/skills/hik-project-md2xlsx/` |
| 个人级 | `~/.cursor/skills/hik-project-md2xlsx/` |

```bash
cp -a hik-project-md2xlsx /path/to/workspace/.cursor/skills/hik-project-md2xlsx
# 或
cp -a hik-project-md2xlsx ~/.cursor/skills/hik-project-md2xlsx
```

## 安装依赖

```bash
pip install openpyxl
```

## 命令行

```bash
python scripts/md_to_xlsx.py input.md output.xlsx
python scripts/md_to_xlsx.py 前盖具身智能上下料技术预研.md "前盖具身智能上下料技术预研 v2.xlsx"
```
