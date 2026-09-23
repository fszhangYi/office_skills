#!/usr/bin/env python3
"""Config-driven geometric FOV coverage (camera-fov-analysis skill).

Usage:
  python analyze_fov.py config.json [--out-dir DIR] [--plot]

Writes:
  fov_summary.json / fov_summary.md
  (optional) fov_angular_compare.png
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n < 1e-12:
        raise ValueError("zero vector")
    return v / n


def load_config(path: Path) -> dict[str, Any]:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    for key in ("lens", "look", "right", "modes", "samples"):
        if key not in cfg:
            raise SystemExit(f"config missing required key: {key}")
    return cfg


def axes(cfg: dict[str, Any]):
    lens = np.asarray(cfg["lens"], dtype=float)
    look = unit(np.asarray(cfg["look"], dtype=float))
    right = unit(np.asarray(cfg["right"], dtype=float))
    if "up" in cfg:
        up = unit(np.asarray(cfg["up"], dtype=float))
    else:
        up = unit(np.cross(look, right))
    # re-orthogonalize right against look
    right = unit(np.cross(up, look))
    return lens, look, right, up


def project(p, lens, look, right, up):
    rel = p - lens
    d = float(rel @ look)
    az = float(np.degrees(np.arctan2(rel @ right, d)))
    el = float(np.degrees(np.arctan2(rel @ up, d)))
    return d, az, el


def in_fov(d: float, az: float, el: float, H: float, V: float) -> bool:
    return d > 1.0 and abs(az) <= H / 2.0 and abs(el) <= V / 2.0


def analyze(cfg: dict[str, Any]) -> dict[str, Any]:
    lens, look, right, up = axes(cfg)
    points = []
    for s in cfg["samples"]:
        xyz = np.asarray(s["xyz"], dtype=float)
        d, az, el = project(xyz, lens, look, right, up)
        points.append(
            {
                "name": s.get("name", ""),
                "tag": s.get("tag", ""),
                "xyz": xyz.tolist(),
                "d_mm": d,
                "az_deg": az,
                "el_deg": el,
            }
        )

    mode_rows = []
    for m in cfg["modes"]:
        H, V = float(m["H_deg"]), float(m["V_deg"])
        flags = []
        for pt in points:
            ok = in_fov(pt["d_mm"], pt["az_deg"], pt["el_deg"], H, V)
            flags.append(ok)
            pt.setdefault("in_fov", {})[m["id"]] = ok
        n_ok = sum(flags)
        tagged = {}
        for tag in sorted({p["tag"] for p in points if p["tag"]}):
            subset = [p for p in points if p["tag"] == tag]
            tagged[tag] = {
                "in": sum(1 for p in subset if p["in_fov"][m["id"]]),
                "n": len(subset),
            }
        hooks_o = [p for p in points if p["tag"] == "hook_o"]
        margin_h = None
        if hooks_o:
            margin_h = H / 2.0 - max(abs(p["az_deg"]) for p in hooks_o)
        mode_rows.append(
            {
                "id": m["id"],
                "label": m.get("label", m["id"]),
                "H_deg": H,
                "V_deg": V,
                "half_H": H / 2.0,
                "half_V": V / 2.0,
                "in_count": n_ok,
                "n": len(points),
                "by_tag": tagged,
                "open_hook_h_margin_deg": margin_h,
            }
        )

    depths = cfg.get("footprint_depths_mm", [90, 118, 120])
    footprints = []
    for m in cfg["modes"]:
        H, V = float(m["H_deg"]), float(m["V_deg"])
        for d in depths:
            footprints.append(
                {
                    "mode": m["id"],
                    "d_mm": d,
                    "width_mm": 2 * d * math.tan(math.radians(H / 2)),
                    "height_mm": 2 * d * math.tan(math.radians(V / 2)),
                }
            )

    return {
        "lens": lens.tolist(),
        "look": look.tolist(),
        "right": right.tolist(),
        "up": up.tolist(),
        "points": points,
        "modes": mode_rows,
        "footprints": footprints,
        "frame": cfg.get("frame", ""),
        "notes": cfg.get("notes", ""),
    }


def write_md(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# FOV geometry summary",
        "",
        f"- Frame: {result.get('frame') or '(unspecified)'}",
        f"- LENS: `{np.round(result['lens'], 3).tolist()}`",
        f"- look: `{np.round(result['look'], 4).tolist()}`",
        "",
        "## Modes",
        "",
        "| id | H×V | half | in/n | open-hook H margin |",
        "| --- | --- | --- | --- | --- |",
    ]
    for m in result["modes"]:
        marg = m["open_hook_h_margin_deg"]
        marg_s = f"{marg:.1f}°" if marg is not None else "—"
        lines.append(
            f"| {m['id']} | {m['H_deg']:.0f}×{m['V_deg']:.0f} | "
            f"±{m['half_H']:.1f}/±{m['half_V']:.1f} | "
            f"{m['in_count']}/{m['n']} | {marg_s} |"
        )
    lines += ["", "## Points", "", "| name | tag | d | az | el |", "| --- | --- | --- | --- | --- |"]
    for p in result["points"]:
        lines.append(
            f"| {p['name']} | {p['tag']} | {p['d_mm']:.1f} | "
            f"{p['az_deg']:.2f} | {p['el_deg']:.2f} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def plot_compare(result: dict[str, Any], path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=140)
    colors = ["#0d6e75", "#1a7a4c", "#c45c26", "#6b4c9a", "#333"]
    for i, m in enumerate(result["modes"]):
        H, V = m["H_deg"], m["V_deg"]
        ax.add_patch(
            Rectangle(
                (-H / 2, -V / 2),
                H,
                V,
                fill=False,
                edgecolor=colors[i % len(colors)],
                lw=1.6,
                label=f"{m['id']} {H:.0f}×{V:.0f}",
            )
        )
    tag_style = {
        "blade": ("o", "#d97816", 18),
        "hook_c": ("o", "#0d6e75", 40),
        "hook_o": ("^", "#6b4c9a", 50),
        "root": ("x", "#c0392b", 55),
    }
    for p in result["points"]:
        mk, c, s = tag_style.get(p["tag"], ("o", "#666", 20))
        ax.scatter([p["az_deg"]], [p["el_deg"]], marker=mk, c=c, s=s, zorder=3)
    ax.axhline(0, color="#bbb", lw=0.8)
    ax.axvline(0, color="#bbb", lw=0.8)
    ax.set_aspect("equal")
    ax.set_xlabel("az / °")
    ax.set_ylabel("el / °")
    ax.set_title("Feature points vs crop FOV boxes")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("config", type=Path)
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--plot", action="store_true")
    args = ap.parse_args()

    cfg = load_config(args.config)
    out = args.out_dir or args.config.resolve().parent / "fov_out"
    out.mkdir(parents=True, exist_ok=True)

    result = analyze(cfg)
    (out / "fov_summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_md(result, out / "fov_summary.md")
    print("wrote", out / "fov_summary.json")
    print("wrote", out / "fov_summary.md")

    for m in result["modes"]:
        print(
            f"  {m['id']}: {m['in_count']}/{m['n']} in FOV; "
            f"open-hook margin={m['open_hook_h_margin_deg']}"
        )

    if args.plot:
        plot_compare(result, out / "fov_angular_compare.png")
        print("wrote", out / "fov_angular_compare.png")


if __name__ == "__main__":
    main()
