#!/usr/bin/env python3
"""Print AutoDL disk usage: overlay (/) vs data disk (/root/autodl-tmp)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

DATA_ROOT = Path("/root/autodl-tmp")
OVERLAY_PATHS = [
    Path("/root/miniconda3"),
    Path("/root/GraspVLA_env"),
    Path("/tmp"),
    Path("/root/.cursor"),
    Path("/root/.cache"),
    Path("/var/cache/apt"),
]


def fmt_gb(nbytes: int) -> str:
    return f"{nbytes / (1024**3):.2f} GiB"


def df_line(mount: str) -> str:
    usage = shutil.disk_usage(mount)
    pct = usage.used / usage.total * 100 if usage.total else 0
    return (
        f"{mount}: total {fmt_gb(usage.total)}, "
        f"used {fmt_gb(usage.used)} ({pct:.0f}%), "
        f"free {fmt_gb(usage.free)}"
    )


def du_x(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        out = subprocess.check_output(
            ["du", "-xsb", str(path)],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return int(out.split()[0])
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return None


def resolve_target(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path


def on_data_disk(path: Path) -> bool:
    if not DATA_ROOT.exists():
        return False
    try:
        return resolve_target(path).is_relative_to(DATA_ROOT.resolve())
    except (ValueError, OSError):
        return str(resolve_target(path)).startswith(str(DATA_ROOT.resolve()))


def main() -> int:
    print("=== AutoDL disk check ===\n")
    print(df_line("/"))
    if DATA_ROOT.exists():
        print(df_line(str(DATA_ROOT)))
    print()

    print("Large paths on overlay (du -x):")
    rows: list[tuple[int, str, str]] = []
    for p in OVERLAY_PATHS:
        nbytes = du_x(p)
        if nbytes is None:
            continue
        flag = "on data disk" if on_data_disk(p) else "OVERLAY"
        if p.is_symlink():
            flag += f" -> {os.readlink(p)}"
        rows.append((nbytes, str(p), flag))

    for p in sorted(Path("/root").iterdir(), key=lambda x: x.name):
        if p.name in ("autodl-tmp", "autodl-pub", ".", ".."):
            continue
        if any(str(p) == str(o) for o in OVERLAY_PATHS):
            continue
        nbytes = du_x(p)
        if nbytes is None or nbytes < 500 * 1024 * 1024:
            continue
        flag = "on data disk" if on_data_disk(p) else "OVERLAY"
        if p.is_symlink():
            flag += f" -> {os.readlink(p)}"
        rows.append((nbytes, str(p), flag))

    rows.sort(reverse=True)
    for nbytes, path, flag in rows:
        print(f"  {fmt_gb(nbytes):>10}  {path}  [{flag}]")

    usage = shutil.disk_usage("/")
    pct = usage.used / usage.total * 100 if usage.total else 0
    if pct >= 90:
        print("\nWARN: system disk >= 90% — run autodl_cleanup.sh --apply")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
