# DeepSeek share API notes

## What worked

`GET https://chat.deepseek.com/api/v0/share/content?share_id=<id>` with a normal browser User-Agent returns JSON. A long chat can be about 1 MB.

```text
code, msg
data.biz_code, data.biz_msg
data.biz_data.title
data.biz_data.model_type
data.biz_data.messages[]:
  message_id, parent_id, role (USER | ASSISTANT)
  fragments[]: { id, type, content }
```

Fragment `type` values seen in a real share: `REQUEST`, `RESPONSE`, `THINK`, `TOOL_SEARCH`, `TOOL_OPEN`, `FILE`, `TIP`. Only `REQUEST` and `RESPONSE` belong in the transcript. `FILE` content may be empty or non-text; keep a short JSON dump if the user asked about an attachment.

Message list order matched the on-screen order. Preserve that order; do not sort by `inserted_at` unless the list is clearly shuffled.

## What failed

| Attempt | Result |
| --- | --- |
| `WebFetch` of the share URL | Open-graph page, no messages |
| `GET /api/v0/share/get_share_message?share_id=` | Same marketing page |
| Browser accessibility snapshot | First screen is "Abnormal usage environment"; after dismiss, refs are mostly citation links |
| `document.body.innerText` | About 23k characters while REQUEST+RESPONSE text was about 86k. The list is virtualized |
| PowerShell `curl -sS` | `curl` is an alias of `Invoke-WebRequest` and rejects those flags. Use `curl.exe` or the Python script |
| Printing the JSON with the default Windows console code page | Chinese looks corrupted. The file is still valid UTF-8 |

The live API URL was found from `performance.getEntriesByType('resource')` after the share page loaded, not from the HTML source.

## Browser fallback

Use this only when `scripts/fetch_share.py` exits because the content API failed.

1. Open `https://chat.deepseek.com/share/<id>`.
2. If a dialog titled "Abnormal usage environment" is up, close it.
3. In the page, read resource URLs and keep the one containing `share` and `content`.
4. `fetch` that URL from the page (it has the site cookies) and save the JSON.
5. Re-run the same REQUEST/RESPONSE filter. Do not summarize from the screenshot.
