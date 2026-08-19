#!/usr/bin/env python3
"""Hard preflight for GraspVLA reproduction.

Prints every check, then either:
  GraspVLA preflight: PASS
or:
  GraspVLA preflight: FAIL
  Exit reasons:
    1. [disk] ...
    2. [cuda] ...

Exit 0 only if the selected phase can proceed. Agents MUST stop on nonzero.

Thresholds follow GraspVLA_手把手复现教程.md (AutoDL split-disk, ~10GB VRAM, cu128).
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

GIB = 1024**3
MIB = 1024**2

# Tutorial §A
SYS_FREE_GIB_ENV = 12.0          # conda + torch unpack peak
DATA_FREE_GIB_FROM_SCRATCH = 25.0
DATA_MARGIN_GIB = 3.0
WEIGHT_BYTES = 12_624_643_076    # model.safetensors
VRAM_MIN_MIB = 10 * 1024         # ~10 GB used on L40s/5090
CUDA_MIN = (12, 0)
CUDA_RECOMMENDED = (12, 8)
CGROUP_CURL_GIB = 8.0            # below this, hf download OOMs; curl is required

HUB_MARKERS = (
    "models--timm--vit_large_patch14_reg4_dinov2.lvd142m",
    "models--timm--vit_so400m_patch14_siglip_224.v2_webli",
    "models--internlm--internlm2-1_8b",
)


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.reasons: list[str] = []
        self.notes: list[str] = []

    def ok(self, msg: str) -> None:
        self.lines.append(f"[ok]   {msg}")

    def fail(self, tag: str, msg: str) -> None:
        self.lines.append(f"[fail] {msg}")
        self.reasons.append(f"[{tag}] {msg}")

    def note(self, msg: str) -> None:
        self.lines.append(f"[note] {msg}")
        self.notes.append(msg)

    def dump(self, phase: str, passed: bool) -> None:
        print("=== GraspVLA preflight ===")
        print(f"phase: {phase}")
        print()
        for line in self.lines:
            print(line)
        print()
        if passed:
            print("GraspVLA preflight: PASS")
            if self.notes:
                print("Notes (non-blocking):")
                for i, n in enumerate(self.notes, 1):
                    print(f"  {i}. {n}")
        else:
            print("GraspVLA preflight: FAIL")
            print("Exit reasons:")
            for i, r in enumerate(self.reasons, 1):
                print(f"  {i}. {r}")
            print()
            print("Fix the items above, then re-run this check. Do not continue install/serve.")


def mount_free_gib(path: Path) -> float:
    probe = path
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    if not probe.exists():
        probe = Path("/")
    return shutil.disk_usage(str(probe)).free / GIB


def read_cgroup_mem_bytes() -> int | None:
    for p in (
        Path("/sys/fs/cgroup/memory.max"),
        Path("/sys/fs/cgroup/memory/memory.limit_in_bytes"),
    ):
        if not p.is_file():
            continue
        raw = p.read_text().strip()
        if raw in ("max", "unlimited"):
            return None
        try:
            val = int(raw)
        except ValueError:
            return None
        # cgroup v1 unset often looks like 2^63-1 or 2^64-1
        if val >= 1 << 60:
            return None
        return val
    return None


def host_mem_available_bytes() -> int | None:
    info = Path("/proc/meminfo")
    if not info.is_file():
        return None
    for line in info.read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    return None


def which(name: str) -> str | None:
    return shutil.which(name)


def run(cmd: list[str], timeout: int = 20) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out.strip()
    except FileNotFoundError:
        return 127, ""
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def parse_cuda_tuple(text: str) -> tuple[int, int] | None:
    parts = text.strip().split(".")
    if not parts or not parts[0].isdigit():
        return None
    major = int(parts[0])
    minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    return major, minor


def nvidia_info() -> dict:
    info: dict = {
        "ok": False,
        "name": None,
        "vram_mib": None,
        "driver": None,
        "cuda": None,
        "error": None,
    }
    if not which("nvidia-smi"):
        info["error"] = "nvidia-smi not found (no NVIDIA driver in PATH)"
        return info
    rc, out = run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ]
    )
    if rc != 0 or not out:
        info["error"] = f"nvidia-smi failed (exit {rc}): {out[:200] or 'no output'}"
        return info
    row = out.splitlines()[0]
    cols = [c.strip() for c in row.split(",")]
    if len(cols) < 3:
        info["error"] = f"unexpected nvidia-smi csv: {row}"
        return info
    info["name"] = cols[0]
    try:
        info["vram_mib"] = float(cols[1])
    except ValueError:
        info["error"] = f"cannot parse VRAM from: {row}"
        return info
    info["driver"] = cols[2]
    rc2, banner = run(["nvidia-smi"])
    cuda = None
    if rc2 == 0:
        for line in banner.splitlines():
            if "CUDA Version:" in line:
                cuda = line.split("CUDA Version:")[-1].split()[0]
                break
    info["cuda"] = cuda
    info["ok"] = True
    return info


def detect_data_root(cli: str | None) -> Path:
    if cli:
        return Path(cli).expanduser().resolve()
    env = os.environ.get("GRASPVLA_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    autodl = Path("/root/autodl-tmp")
    if autodl.is_dir():
        return (autodl / "GraspVLA_repro").resolve()
    return (Path.cwd() / "GraspVLA_repro").resolve()


def detect_sys_env() -> Path:
    env = os.environ.get("GRASPVLA_ENV")
    if env:
        return Path(env).expanduser().resolve()
    return Path("/root/GraspVLA_env")


def weights_ready(root: Path) -> bool:
    p = root / "weights" / "checkpoint" / "model.safetensors"
    try:
        return p.is_file() and p.stat().st_size == WEIGHT_BYTES
    except OSError:
        return False


def hub_ready(root: Path) -> bool:
    hub = root / "hf_home" / "hub"
    if not hub.is_dir():
        return False
    for name in HUB_MARKERS:
        d = hub / name
        if not d.is_dir():
            return False
        snaps = list((d / "snapshots").glob("*"))
        if not snaps:
            return False
    incompletes = list(hub.rglob("*.incomplete")) + list(hub.rglob("*.part"))
    return not incompletes


def env_has_torch(env: Path) -> bool:
    py = env / "bin" / "python"
    if not py.is_file():
        return False
    rc, out = run([str(py), "-c", "import torch; print(torch.__version__, torch.cuda.is_available())"])
    return rc == 0 and "True" in out


def find_conda() -> str | None:
    for name in ("conda",):
        w = which(name)
        if w:
            return w
    for p in (
        Path("/root/miniconda3/bin/conda"),
        Path("/opt/conda/bin/conda"),
        Path.home() / "miniconda3/bin/conda",
        Path.home() / "anaconda3/bin/conda",
    ):
        if p.is_file():
            return str(p)
    return None


def check_os(rep: Report) -> None:
    sysname = platform.system().lower()
    machine = platform.machine().lower()
    if sysname != "linux":
        rep.fail("os", f"OS is {platform.system()} {machine}; tutorial assumes Linux x86_64")
        return
    if machine not in ("x86_64", "amd64"):
        rep.fail("os", f"arch is {machine}; tutorial torch wheels are manylinux x86_64")
        return
    rep.ok(f"linux {machine}")


def check_tools(rep: Report, phase: str) -> None:
    for name in ("git", "curl"):
        w = which(name)
        if w:
            rep.ok(f"{name}: {w}")
        else:
            rep.fail("tool", f"{name} not found in PATH (required to clone/download)")
    if phase in ("download", "all"):
        return
    # serve/all extra: conda or existing env checked later


def check_memory(rep: Report, phase: str) -> None:
    cg = read_cgroup_mem_bytes()
    avail = host_mem_available_bytes()
    if avail is not None:
        rep.ok(f"host MemAvailable: {avail / GIB:.1f} GiB (do not treat this as the cgroup limit)")
    if cg is None:
        rep.ok("cgroup memory: unlimited / not set")
        return
    cg_gib = cg / GIB
    msg = f"cgroup memory.max: {cg_gib:.2f} GiB"
    if cg_gib < CGROUP_CURL_GIB:
        rep.note(
            f"{msg} — hf download will OOM (exit 137); must use curl / "
            "scripts/hf_hub_curl_download.py (tutorial §F / §G.1.1)"
        )
        if phase in ("serve", "all") and cg_gib < 1.5:
            rep.fail(
                "memory",
                f"{msg} is too small to load GraspVLA weights into the process; "
                "raise the container/cgroup limit or run serve outside this sandbox",
            )
        else:
            rep.ok(msg + " (download-with-curl is OK)")
    else:
        rep.ok(msg)


def check_disks(rep: Report, phase: str, data_root: Path, env_path: Path) -> None:
    try:
        sys_free = shutil.disk_usage("/").free / GIB
    except OSError as e:
        rep.fail("disk", f"cannot stat system disk /: {e}")
        return
    data_free = mount_free_gib(data_root)

    have_w = weights_ready(data_root)
    have_h = hub_ready(data_root)
    have_env = env_has_torch(env_path)

    need_data = DATA_FREE_GIB_FROM_SCRATCH
    if have_w:
        need_data -= 13.0
    if have_h:
        need_data -= 7.0
    need_data = max(need_data, DATA_MARGIN_GIB)

    need_sys = SYS_FREE_GIB_ENV
    if phase == "download":
        need_sys = 1.0  # weights go to the data disk
    elif have_env:
        need_sys = 2.0

    data_label = str(data_root)
    if sys_free + 1e-6 < need_sys:
        extra = ""
        if not have_env and phase != "download":
            extra = " — clear /root/.cache/pip/http-v2 and /tmp/pip-unpack-* first"
        rep.fail(
            "disk",
            f"system disk / free {sys_free:.1f} GiB < required {need_sys:.0f} GiB "
            f"(conda+torch unpack peak){extra}",
        )
    else:
        rep.ok(f"system disk / free {sys_free:.1f} GiB >= {need_sys:.0f} GiB")

    if data_free + 1e-6 < need_data:
        hint = []
        if not have_w:
            hint.append("weights 12.6GB missing")
        if not have_h:
            hint.append("HF hub cache missing")
        extra = f" ({', '.join(hint)})" if hint else ""
        rep.fail(
            "disk",
            f"data disk at {data_label} free {data_free:.1f} GiB < required {need_data:.0f} GiB{extra}",
        )
    else:
        bits = []
        if have_w:
            bits.append("weights present")
        if have_h:
            bits.append("hub cache present")
        extra = f" ({', '.join(bits)})" if bits else " (from-scratch budget)"
        rep.ok(f"data disk {data_label} free {data_free:.1f} GiB >= {need_data:.0f} GiB{extra}")

    tmp = Path("/tmp")
    try:
        unpack = list(tmp.glob("pip-unpack-*")) + list(tmp.glob("pip-install-*"))
        if unpack:
            size = sum(f.stat().st_size for f in unpack if f.is_file())
            # include dirs roughly
            total = 0
            for p in unpack:
                if p.is_dir():
                    for root, _dirs, files in os.walk(p):
                        for fn in files:
                            try:
                                total += (Path(root) / fn).stat().st_size
                            except OSError:
                                pass
                elif p.is_file():
                    total += p.stat().st_size
            if total > GIB:
                rep.note(
                    f"/tmp has leftover pip-unpack/install (~{total / GIB:.1f} GiB); "
                    "delete them if system disk is tight"
                )
    except OSError:
        pass


def check_cuda(rep: Report, phase: str) -> None:
    info = nvidia_info()
    if phase == "download":
        if info["ok"]:
            rep.ok(
                f"GPU present (not required for download): {info['name']}, "
                f"{info['vram_mib']:.0f} MiB, driver {info['driver']}, "
                f"CUDA {info['cuda'] or '?'}"
            )
        else:
            rep.ok("no GPU — OK for download phase (clone + curl weights/hub only)")
        return

    if not info["ok"]:
        rep.fail(
            "cuda",
            f"{info['error']}. serve / offline_test need an NVIDIA GPU "
            f"with ≥{VRAM_MIN_MIB // 1024} GB VRAM",
        )
        return

    rep.ok(f"GPU {info['name']}, driver {info['driver']}")
    vram = info["vram_mib"]
    if vram + 1e-6 < VRAM_MIN_MIB:
        rep.fail(
            "cuda",
            f"GPU VRAM {vram:.0f} MiB < required {VRAM_MIN_MIB} MiB "
            f"(~10 GB used to load GraspVLA)",
        )
    else:
        rep.ok(f"GPU VRAM {vram:.0f} MiB >= {VRAM_MIN_MIB} MiB")

    cuda = parse_cuda_tuple(info["cuda"] or "")
    if cuda is None:
        rep.fail("cuda", "cannot parse driver CUDA Version from nvidia-smi")
        return
    if cuda < CUDA_MIN:
        rep.fail(
            "cuda",
            f"driver CUDA {info['cuda']} < {CUDA_MIN[0]}.{CUDA_MIN[1]} "
            "(tutorial installs torch 2.7.1+cu128)",
        )
    elif cuda < CUDA_RECOMMENDED:
        rep.note(
            f"driver CUDA {info['cuda']} < recommended 12.8; "
            "cu128 wheels may fail — pick a torch index that matches the driver"
        )
        rep.ok(f"driver CUDA {info['cuda']} >= {CUDA_MIN[0]}.{CUDA_MIN[1]}")
    else:
        rep.ok(f"driver CUDA {info['cuda']} (cu128 OK)")


def check_python_env(rep: Report, phase: str, env_path: Path) -> None:
    if phase == "download":
        conda = find_conda()
        if conda:
            rep.ok(f"conda (not needed until GPU/env stage): {conda}")
        else:
            rep.note("conda not found — OK until you create the Python 3.9 env")
        return

    if env_has_torch(env_path):
        rep.ok(f"existing env with torch+CUDA: {env_path}")
        return

    conda = find_conda()
    if conda:
        rep.ok(f"conda for creating Python 3.9.19 env: {conda}")
        if env_path.exists() and not (env_path / "bin" / "python").is_file():
            rep.note(f"{env_path} exists but has no python — recreate or pick another GRASPVLA_ENV")
        return

    py = which("python3") or which("python")
    if py:
        rc, ver = run([py, "-V"])
        rep.fail(
            "env",
            f"no conda and no usable GraspVLA env at {env_path}; "
            f"found {ver or py} but tutorial needs conda Python 3.9.19 + cu128 torch",
        )
    else:
        rep.fail("env", f"no conda and no python; cannot create {env_path}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="GraspVLA install/serve preflight (hard gate)")
    ap.add_argument(
        "--phase",
        choices=("download", "serve", "all"),
        default="all",
        help="download: no GPU required; serve/all: GPU + VRAM + CUDA required",
    )
    ap.add_argument("--data-root", default=None, help="GraspVLA_repro directory (weights/hf_home)")
    ap.add_argument(
        "--env-path",
        default=None,
        help="conda prefix (default /root/GraspVLA_env or $GRASPVLA_ENV)",
    )
    args = ap.parse_args(argv)

    data_root = detect_data_root(args.data_root)
    env_path = Path(args.env_path).expanduser().resolve() if args.env_path else detect_sys_env()
    phase = args.phase

    rep = Report()
    rep.ok(f"data-root: {data_root}")
    rep.ok(f"env-path: {env_path}")

    check_os(rep)
    check_tools(rep, phase)
    check_memory(rep, phase)
    check_disks(rep, phase, data_root, env_path)
    check_cuda(rep, phase)
    check_python_env(rep, phase, env_path)

    passed = not rep.reasons
    rep.dump(phase, passed)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
