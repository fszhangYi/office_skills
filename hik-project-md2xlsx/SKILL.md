---
name: hik-project-md2xlsx
description: >-
  Convert Chinese 立项/预研 Markdown into 立项报告.xlsx (2-column label|body,
  微软雅黑, auto row height, GFM tables→numbered lists, merged 建议与下一步).
  Use when the user asks md→xlsx, 转成立项报告, 生成预研表, hik-project-md2xlsx,
  or to build 前盖*技术预研*.xlsx / *立项报告*.xlsx from .md.
---

# hik-project-md2xlsx — Markdown → 立项报告 XLSX

把预研/立项 Markdown 导出为与 `前盖具身智能上下料技术预研.xlsx` 同构的两列表。

## When to use

- User asks `md→xlsx` / `转成立项报告` / `生成预研 xlsx` / `hik-project-md2xlsx`
- Building `*技术预研*.xlsx`、`*立项报告*.xlsx` from an edited `.md`

## Output layout

详见 [format.md](format.md)。硬规则：

1. 两列：A 栏目 / B 正文；字体微软雅黑 11
2. 每个 `##`、`###` → 一行（长文用 `###` 拆行，避免超 Excel 行高上限 ≈409pt）
3. **GFM 表格不得原样塞进单元格**；脚本转成编号条目（三列：`1. 维度：边界；说明`；四列主备矩阵：`保留/晋升` + `退出/降级`）
4. 「建议与下一步计划」：首段摘要 + 余下条目 → A 列合并两行
5. 「提出日期」：解析为 Excel 日期
6. 行高按 B 列内容估算（保守换行宽度），上限 400pt；超长栏目自动拆为 `原标题` / `原标题（续1）` …

## Markdown expectations

```markdown
# 文档标题

## 预研名称
《……》

## 提出日期
2026-08-01

## 技术升级
……

### 约定来料边界
（可选：### 单独成行，利于行高）

| 维度 | 建议边界 | 说明 |
| --- | --- | --- |
| … | … | … |

## 建议与下一步计划
建议批准立项，……

1. …
2. …
```

## How to convert

Prefer the bundled script（勿手写版式）：

```bash
pip install openpyxl -q
python scripts/md_to_xlsx.py /path/to/input.md /path/to/output.xlsx
```

Example：

```bash
python .cursor/skills/hik-project-md2xlsx/scripts/md_to_xlsx.py \
  前盖具身智能上下料技术预研.md \
  "前盖具身智能上下料技术预研 v2.xlsx"
```

## Agent checklist

1. Confirm input `.md` and output `.xlsx` name
2. Long sections：优先用 `###` 拆栏，避免单行裁切
3. Run `scripts/md_to_xlsx.py`
4. Spot-check：无 `|` 管道表残留、行高可读、「建议与下一步」合并、日期格式
5. Dependencies: `openpyxl` only
6. Reverse → **hik-project-xlsx2md**
