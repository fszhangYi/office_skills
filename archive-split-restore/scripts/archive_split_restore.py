#!/usr/bin/env python3
"""Split / restore large archives by raw byte chunks (no decompress).

Supports common package suffixes; unknown extensions allowed with --force.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import math
import os
import sys
import tarfile
import zipfile
from pathlib import Path

# Longer compound suffixes first
COMPOUND_SUFFIXES = (
    ".tar.gz",
    ".tar.bz2",
    ".tar.xz",
    ".tar.zst",
    ".tgz",
    ".tbz2",
    ".txz",
)

SIMPLE_SUFFIXES = (
    ".gz",
    ".bz2",
    ".xz",
    ".zst",
    ".tar",
    ".zip",
    ".7z",
    ".rar",
    ".iso",
    ".dmg",
    ".whl",
    ".deb",
    ".rpm",
)

DEFAULT_CHUNK_MB = 80
CHUNK_EXT = ".archunk"


def split_name(path: Path) -> tuple[str, str]:
    """Return (stem_without_archive_suffix, full_suffix including dot)."""
    name = path.name
    lower = name.lower()
    for suf in COMPOUND_SUFFIXES:
        if lower.endswith(suf):
            return name[: -len(suf)], name[-len(suf) :]
    for suf in SIMPLE_SUFFIXES:
        if lower.endswith(suf):
            return name[: -len(suf)], name[-len(suf) :]
    # generic: last suffix or empty
    if path.suffix:
        return path.stem, path.suffix
    return name, ""


def is_supported(path: Path, force: bool) -> bool:
    if force:
        return True
    lower = path.name.lower()
    return any(lower.endswith(s) for s in COMPOUND_SUFFIXES + SIMPLE_SUFFIXES)


def write_metadata(path: Path, meta: dict[str, str | int]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for k, v in meta.items():
            f.write(f"{k}={v}\n")


def read_metadata(path: Path) -> dict[str, str]:
    meta: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                meta[k] = v
    return meta


def sha256_file(path: Path, bufsize: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(bufsize)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def split_archive(
    input_file: Path,
    chunk_size_mb: int = DEFAULT_CHUNK_MB,
    output_dir: Path | None = None,
    force: bool = False,
) -> bool:
    if not input_file.is_file():
        print(f"错误: 文件不存在: {input_file}")
        return False
    if not is_supported(input_file, force):
        print(
            f"错误: 不支持的后缀 {input_file.suffix!r}。"
            f"可用 --force，或使用已知格式: {', '.join(COMPOUND_SUFFIXES + SIMPLE_SUFFIXES)}"
        )
        return False

    stem, ext = split_name(input_file)
    out = output_dir or Path(f"{stem}_chunks")
    out.mkdir(parents=True, exist_ok=True)

    total_size = input_file.stat().st_size
    chunk_size = max(1, chunk_size_mb) * 1024 * 1024
    num_chunks = max(1, math.ceil(total_size / chunk_size)) if total_size else 1

    print(f"分割: {input_file}")
    print(f"大小: {total_size / (1024 * 1024):.2f} MB → {num_chunks} 块 × ~{chunk_size_mb} MB")
    print(f"输出: {out}")

    digest = hashlib.sha256()
    with input_file.open("rb") as src:
        for i in range(num_chunks):
            remaining = chunk_size
            chunk_path = out / f"{stem}.part{i:03d}{CHUNK_EXT}"
            written = 0
            with chunk_path.open("wb") as dst:
                while remaining > 0:
                    buf = src.read(min(1024 * 1024, remaining))
                    if not buf:
                        break
                    dst.write(buf)
                    digest.update(buf)
                    written += len(buf)
                    remaining -= len(buf)
            print(f"  [{i + 1}/{num_chunks}] {chunk_path.name} ({written / (1024 * 1024):.2f} MB)")

    meta = {
        "original_name": stem,
        "original_filename": input_file.name,
        "total_chunks": num_chunks,
        "chunk_size_mb": chunk_size_mb,
        "total_size": total_size,
        "original_extension": ext,
        "chunk_ext": CHUNK_EXT,
        "sha256": digest.hexdigest(),
        "format": "raw-byte-split-v1",
    }
    meta_path = out / f"{stem}.metadata"
    write_metadata(meta_path, meta)
    print(f"完成。元数据: {meta_path}")
    return True


def restore_archive(
    chunks_dir: Path,
    output_file: Path | None = None,
    verify_format: bool = True,
) -> bool:
    if not chunks_dir.is_dir():
        print(f"错误: 目录不存在: {chunks_dir}")
        return False

    metas = list(chunks_dir.glob("*.metadata"))
    if not metas:
        print("错误: 找不到 .metadata 文件")
        return False
    meta = read_metadata(metas[0])

    stem = meta.get("original_name")
    total_chunks = int(meta.get("total_chunks", "0"))
    total_size = int(meta.get("total_size", "0"))
    ext = meta.get("original_extension", "")
    chunk_ext = meta.get("chunk_ext", CHUNK_EXT)
    expect_sha = meta.get("sha256", "")

    # Legacy: .gzchunk / .tarchunk from older scripts
    if not stem or total_chunks <= 0:
        print("错误: 元数据损坏")
        return False

    if output_file is None:
        output_file = Path(f"{stem}_restored{ext}")

    print(f"恢复: {stem}{ext} ← {total_chunks} 块 → {output_file}")

    digest = hashlib.sha256()
    with output_file.open("wb") as out:
        for i in range(total_chunks):
            candidates = [
                chunks_dir / f"{stem}.part{i:03d}{chunk_ext}",
                chunks_dir / f"{stem}.part{i:03d}.gzchunk",
                chunks_dir / f"{stem}.part{i:03d}.tarchunk",
                chunks_dir / f"{stem}.part{i:03d}.archunk",
            ]
            chunk_path = next((p for p in candidates if p.is_file()), None)
            if chunk_path is None:
                print(f"错误: 缺少块 part{i:03d}")
                return False
            with chunk_path.open("rb") as cf:
                while True:
                    buf = cf.read(1024 * 1024)
                    if not buf:
                        break
                    out.write(buf)
                    digest.update(buf)
            print(f"  [{i + 1}/{total_chunks}] {chunk_path.name}")

    restored = output_file.stat().st_size
    ok = restored == total_size
    if ok:
        print(f"大小校验通过: {restored} 字节")
    else:
        print(f"警告: 大小不匹配 期望={total_size} 实际={restored}")

    if expect_sha:
        got = digest.hexdigest()
        if got == expect_sha:
            print(f"SHA256 校验通过: {got}")
        else:
            print(f"警告: SHA256 不匹配\n  期望 {expect_sha}\n  实际 {got}")
            ok = False

    if verify_format:
        _soft_validate(output_file, ext)

    print(f"{'成功' if ok else '完成(有警告)'}: {output_file}")
    return ok


def _soft_validate(path: Path, ext: str) -> None:
    e = ext.lower()
    try:
        if e in {".gz"} or e.endswith(".gz"):
            # .tar.gz also ends with .gz — try gzip header read
            with gzip.open(path, "rb") as f:
                f.read(1)
            print("格式抽检: gzip 可读")
        elif e == ".tar":
            with tarfile.open(path, "r:") as t:
                n = len(t.getmembers())
            print(f"格式抽检: tar 成员数={n}")
        elif e == ".zip":
            with zipfile.ZipFile(path, "r") as z:
                bad = z.testzip()
            if bad:
                print(f"警告: zip 损坏成员 {bad}")
            else:
                print("格式抽检: zip OK")
        elif e in {".tar.gz", ".tgz"}:
            with tarfile.open(path, "r:gz") as t:
                n = len(t.getmembers())
            print(f"格式抽检: tar.gz 成员数={n}")
    except Exception as exc:
        print(f"警告: 格式抽检失败（仍可能是有效字节合并）: {exc}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="按字节分割/恢复打包或压缩文件（不解压内容）"
    )
    p.add_argument("mode", choices=["split", "restore"])
    p.add_argument("path", help="split=源文件；restore=块目录")
    p.add_argument("-s", "--size", type=int, default=DEFAULT_CHUNK_MB, help="每块大小 MB")
    p.add_argument("-o", "--output", help="restore 输出路径，或 split 输出目录")
    p.add_argument(
        "--force",
        action="store_true",
        help="允许任意后缀（按原始字节切分）",
    )
    p.add_argument(
        "--no-verify-format",
        action="store_true",
        help="restore 时跳过 gzip/tar/zip 抽检",
    )
    args = p.parse_args(argv)

    if args.mode == "split":
        out_dir = Path(args.output) if args.output else None
        ok = split_archive(Path(args.path), args.size, out_dir, force=args.force)
    else:
        out = Path(args.output) if args.output else None
        ok = restore_archive(
            Path(args.path), out, verify_format=not args.no_verify_format
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
