---
name: deepseek-share-to-md
description: >-
  Extract a DeepSeek shared chat (chat.deepseek.com/share/<id>) from the public
  share content API and write a focused Markdown summary. Use when the user
  pastes a DeepSeek share URL, asks to 总结 DeepSeek 分享对话, 分享链接转 md,
  or save chat.deepseek.com/share content. Do not scrape the rendered share page.
---

# DeepSeek share → Markdown

The share HTML page is a shell. The transcript is JSON from:

`https://chat.deepseek.com/api/v0/share/content?share_id=<id>`

`<id>` is the last path segment of `https://chat.deepseek.com/share/<id>`. The endpoint is public; no login cookie is required.

## When to use

- User pastes `chat.deepseek.com/share/...` and asks for a summary, notes, or an `.md` file
- User says 总结 DeepSeek 分享 / 分享对话转 md

## Do not

- Do not treat the rendered page, a browser snapshot, or `WebFetch` of the share URL as the transcript. The page shows an "Abnormal usage environment" dialog, then virtualizes messages. `document.body.innerText` is a partial prefix.
- Do not call `/api/v0/share/get_share_message`. That URL returns the marketing page, not the chat.
- On Windows PowerShell, `curl` is `Invoke-WebRequest`. Do not pass curl flags to it. The script uses the stdlib instead.
- Do not judge Chinese text from a console that is not UTF-8. Write files as UTF-8.
- Do not leave the raw transcript in the user's project unless they asked to keep it.

## Pipeline

```
Task Progress:
- [ ] 1. Run scripts/fetch_share.py
- [ ] 2. Read the transcript (REQUEST/RESPONSE only)
- [ ] 3. Write a topical Markdown summary
- [ ] 4. Delete the transcript
```

From the `office_skills` repo (or the installed skill directory):

```bash
python scripts/fetch_share.py "https://chat.deepseek.com/share/<id>" /tmp/deepseek-share.txt
```

The script prints `share_id`, the output path, byte size, and one line per user turn. It keeps fragment types `REQUEST` and `RESPONSE` only, and drops `THINK`, `TOOL_SEARCH`, `TOOL_OPEN`, and `TIP`.

JSON shape: `data.biz_data.messages[]` with `role` and `fragments[].{type,content}`. If `code` is not 0 or `messages` is missing, the share API changed — stop and say so. Browser fallback is in [reference.md](reference.md).

## Write the Markdown

Summarize the topic the user named. Skip unrelated turns (a long share often starts on a different subject).

- Lead with the conclusion and the architecture, then hardware, procedure, limits.
- Keep numbers, part numbers, and pinouts that the answers actually stated. Do not invent specs.
- Say the figures come from that shared chat and still need a datasheet or a measurement.
- Put the share URL at the top.
- Write the file where the user asked. If they did not name a path, use the current workspace and a short Chinese or English filename that names the topic.
- After the summary file exists, delete the transcript from step 1.

## Output shape

```markdown
# <topic>

来源：[DeepSeek 分享对话](https://chat.deepseek.com/share/<id>)。

## 结论
...

## 方案
...

## 边界
- ...
```
