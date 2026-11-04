# deepseek-share-to-md

Cursor Agent Skill：从 DeepSeek 分享链接（`chat.deepseek.com/share/<id>`）拉取公开的 share content JSON，抽出问答正文，再写成聚焦的 Markdown。

不要抓分享页 HTML。页面会先弹出异常环境提示，正文还是虚拟列表，看到的只是开头一段。

## 安装位置

| 类型 | 路径 |
| --- | --- |
| 项目级 | `<工作区>/.cursor/skills/deepseek-share-to-md/` |
| 个人级 | `~/.cursor/skills/deepseek-share-to-md/` |

```bash
cp -a deepseek-share-to-md ~/.cursor/skills/deepseek-share-to-md
```

只需 Python 3 标准库。

## 命令行

```bash
python scripts/fetch_share.py https://chat.deepseek.com/share/<id> /tmp/deepseek-share.txt
```

stdout 是用户每轮问题的索引。正文在输出文件里，编码为 UTF-8。
