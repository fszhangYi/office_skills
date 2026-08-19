#!/usr/bin/env python3
"""Populate Hugging Face hub cache with curl (low RAM; no huggingface_hub).

Layout written (huggingface_hub compatible):
  $HF_HOME/hub/models--org--name/{blobs,refs,snapshots}

Skips pytorch_model.bin when model.safetensors exists (timm prefers safetensors).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

HF_API = "https://huggingface.co"


def _opener() -> urllib.request.OpenerDirector:
    proxy = os.environ.get("https_proxy") or os.environ.get("http_proxy")
    handlers = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    return urllib.request.build_opener(*handlers)


def api_json(path: str) -> Any:
    url = HF_API + path
    req = urllib.request.Request(url, headers={"User-Agent": "graspvla-repro/1.0"})
    with _opener().open(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def repo_folder_name(repo_id: str) -> str:
    return "models--" + repo_id.replace("/", "--")


def list_files(repo_id: str) -> List[Dict[str, Any]]:
    data = api_json(f"/api/models/{repo_id}/tree/main?recursive=1")
    return [x for x in data if x.get("type") == "file"]


def blob_id_for(entry: Dict[str, Any]) -> str:
    lfs = entry.get("lfs") or {}
    if lfs.get("oid"):
        oid = str(lfs["oid"])
        if oid.startswith("sha256:"):
            oid = oid.split(":", 1)[1]
        return oid
    return str(entry["oid"])


def should_skip(path: str, names: Iterable[str]) -> bool:
    names_set = set(names)
    # Prefer safetensors over duplicate pytorch bins
    if path.endswith("pytorch_model.bin") and path.replace("pytorch_model.bin", "model.safetensors") in names_set:
        return True
    return False


def curl_download(url: str, dest: Path, expected: int = 0) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    if dest.exists():
        if expected and dest.stat().st_size == expected and not tmp.exists():
            return
        if not tmp.exists():
            # incomplete/wrong-size final file: restart into .part
            dest.unlink()
    cmd = [
        "curl",
        "-sS",
        "--no-progress-meter",
        "-L",
        "--fail",
        "--retry",
        "40",
        "--retry-delay",
        "8",
        "--connect-timeout",
        "30",
        "-C",
        "-",
        "--output",
        str(tmp),
        url,
    ]
    print(f"GET {url} -> {dest}", flush=True)
    subprocess.check_call(cmd)
    tmp.replace(dest)


def link_snapshot(snap_root: Path, rel: str, blob: Path) -> None:
    target = snap_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    rel_blob = os.path.relpath(blob, start=target.parent)
    if target.is_symlink() or target.exists():
        target.unlink()
    target.symlink_to(rel_blob)


def download_repo(repo_id: str, hf_home: Path) -> None:
    info = api_json(f"/api/models/{repo_id}")
    commit = info.get("sha") or info.get("siblings", [None])
    if not isinstance(commit, str):
        # fallback: first file HEAD is handled below
        commit = None
    files = list_files(repo_id)
    names = [f["path"] for f in files]
    selected = [f for f in files if not should_skip(f["path"], names)]
    storage = hf_home / "hub" / repo_folder_name(repo_id)
    blobs = storage / "blobs"
    blobs.mkdir(parents=True, exist_ok=True)
    (storage / "refs").mkdir(parents=True, exist_ok=True)

    if commit is None:
        raise SystemExit(f"cannot resolve commit for {repo_id}: {info.keys()}")

    snap = storage / "snapshots" / commit
    snap.mkdir(parents=True, exist_ok=True)
    (storage / "refs" / "main").write_text(commit + "\n")

    print(f"==> {repo_id} commit={commit} files={len(selected)}/{len(files)}", flush=True)
    for entry in selected:
        rel = entry["path"]
        bid = blob_id_for(entry)
        blob = blobs / bid
        url = f"{HF_API}/{repo_id}/resolve/main/{rel}"
        expected = int(entry.get("size") or 0)
        if blob.exists() and expected and blob.stat().st_size == expected:
            print(f"skip (complete) {rel} {expected}", flush=True)
        else:
            curl_download(url, blob, expected=expected)
            if expected and blob.stat().st_size != expected:
                raise SystemExit(
                    f"size mismatch {rel}: got {blob.stat().st_size} expected {expected}"
                )
        link_snapshot(snap, rel, blob)
    print(f"done {repo_id} -> {storage}", flush=True)


def main(argv: List[str]) -> int:
    if len(argv) < 3:
        print("usage: hf_hub_curl_download.py HF_HOME REPO_ID [REPO_ID...]", file=sys.stderr)
        return 2
    hf_home = Path(argv[1])
    for repo in argv[2:]:
        download_repo(repo, hf_home)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
