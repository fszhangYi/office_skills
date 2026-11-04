#!/usr/bin/env python3
"""Download a DeepSeek shared chat and write REQUEST/RESPONSE text as UTF-8.

The share HTML page is not the transcript. The SPA loads:

    https://chat.deepseek.com/api/v0/share/content?share_id=<id>

Usage:
    python scripts/fetch_share.py https://chat.deepseek.com/share/<id> [out.txt]
    python scripts/fetch_share.py <id>
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://chat.deepseek.com/api/v0/share/content?share_id={share_id}"
SHARE_URL_RE = re.compile(r"share/([A-Za-z0-9]{8,64})(?:/|$|\?)")
SHARE_ID_RE = re.compile(r"^[A-Za-z0-9]{8,64}$")
KEEP_TYPES = {"REQUEST", "RESPONSE"}


def share_id_from(raw: str) -> str:
    text = raw.strip().rstrip("/")
    match = SHARE_URL_RE.search(text)
    if match:
        return match.group(1)
    if SHARE_ID_RE.fullmatch(text):
        return text
    raise SystemExit(f"cannot parse share id from: {raw}")


def fetch_json(share_id: str) -> dict:
    url = API.format(share_id=share_id)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read(400).decode("utf-8", "replace")
        raise SystemExit(f"HTTP {exc.code} from {url}\n{detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"request failed: {exc}") from exc
    try:
        data = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"response is not JSON ({len(body)} bytes)") from exc
    if data.get("code") not in (0, None):
        raise SystemExit(f"api code={data.get('code')} msg={data.get('msg')!r}")
    biz = (data.get("data") or {}).get("biz_data")
    if not isinstance(biz, dict) or not isinstance(biz.get("messages"), list):
        raise SystemExit(
            f"JSON has no data.biz_data.messages for share_id={share_id}; share API shape changed"
        )
    return data


def fragment_text(fragment: dict) -> str:
    content = fragment.get("content")
    if isinstance(content, str):
        return content
    if content is None:
        return ""
    return json.dumps(content, ensure_ascii=False)


def render(data: dict, share_id: str) -> tuple[str, list[tuple[int, str]]]:
    biz = data["data"]["biz_data"]
    title = biz.get("title") or "Shared Conversation"
    messages = biz["messages"]
    parts = [
        f"source: https://chat.deepseek.com/share/{share_id}",
        f"title: {title}",
        f"messages: {len(messages)}",
        "",
    ]
    questions: list[tuple[int, str]] = []
    for index, message in enumerate(messages):
        role = message.get("role") or "?"
        chunks = [
            fragment_text(fragment)
            for fragment in message.get("fragments") or []
            if fragment.get("type") in KEEP_TYPES
        ]
        chunks = [chunk for chunk in chunks if chunk.strip()]
        if not chunks:
            continue
        text = "\n".join(chunks)
        parts.append(f"===== {index:02d} {role} len={len(text)} =====")
        parts.append(text)
        parts.append("")
        if role == "USER":
            questions.append((index, text.replace("\n", " ")[:300]))
    return "\n".join(parts).rstrip() + "\n", questions


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(argv) < 2 or argv[1] in {"-h", "--help"}:
        print(__doc__.strip())
        return 0 if len(argv) > 1 else 2
    share_id = share_id_from(argv[1])
    out = Path(argv[2]) if len(argv) > 2 else Path(f"_deepseek_share_{share_id}.txt")
    data = fetch_json(share_id)
    transcript, questions = render(data, share_id)
    out.write_text(transcript, encoding="utf-8")
    print(f"share_id={share_id}")
    print(f"wrote {out.resolve()} ({len(transcript.encode('utf-8'))} bytes)")
    print(f"user_turns={len(questions)}")
    for index, question in questions:
        print(f"{index:02d} {question}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
