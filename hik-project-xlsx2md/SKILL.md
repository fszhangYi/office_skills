---
name: hik-project-xlsx2md
description: >-
  Convert Chinese 立项/预研 report XLSX (2-column label|body 立项报告 layout)
  to Markdown with ## sections. Use when the user asks xlsx→md, 立项报告转 md,
  预研表转 Markdown, or to restore 前盖*技术预研*.xlsx / *立项*.xlsx to .md.
---

# 立项报告 XLSX → Markdown

与 **hik-project-md2xlsx** 配对：把两列立项/预研表还原成可编辑 Markdown。

## When to use

- User asks `xlsx→md` / `转成 md` / `立项报告转 Markdown`
- Restoring `*技术预研*.xlsx`、`*立项*.xlsx`、`前盖具身智能上下料技术预研*.xlsx`

## Layout assumed（立项报告表）

详见 [format.md](format.md)。要点：

1. 单表两列：A=栏目名，B=正文
2. 微软雅黑、自动换行；末栏「建议与下一步计划」常见 A 列跨两行合并
3. 日期单元格输出为 `YYYY-MM-DD`

## Conversion rules

1. 每个 A 栏目 → `## 栏目名`（去掉换行与多余空白）
2. 合并单元格：同一标签下多行 B 用空行拼接，仍归一个 `##`
3. 若存在「预研名称 / 项目名称」，其 B 文去书名号后作文档 `#` 标题
4. **不**把 B 里的编号列表臆造回 GFM 表（保持列表原文）
5. 默认输出：与输入同目录、同主文件名 `.md`

## How to convert

```bash
pip install openpyxl -q
python scripts/xlsx_to_md.py /path/to/input.xlsx /path/to/output.md
```

同名输出：

```bash
python scripts/xlsx_to_md.py "前盖具身智能上下料技术预研 v2.xlsx"
# → 前盖具身智能上下料技术预研 v2.md
```

## Agent checklist

1. Confirm input `.xlsx` and output `.md`
2. Run `scripts/xlsx_to_md.py`
3. Spot-check：`#` 标题、各 `##`、合并栏「建议与下一步」、日期
4. Dependencies: `openpyxl` only
5. Reverse direction → **hik-project-md2xlsx**
