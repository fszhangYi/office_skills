---
name: solidworks-2025-python-com
description: >-
  SolidWorks 2025 Python COM automation with pywin32 (FeatureExtrusion2,
  FeatureCut4, InsertRefPlane, Move/Copy body, FeatureFillet, STEP import,
  templates). Use when writing or debugging SolidWorks scripts, SldWorks.Application,
  create_l_clamp, sw_helper, GB_Part templates, or SW 2025 COM failures.
---

# SolidWorks 2025 + Python COM

Hard-won rules from EFG wrist `sw/` automation on **SolidWorks 2025 SP1** + **Python 3.12 64-bit** + **pywin32**. Prefer these over generic SW API blog posts.

## When to apply

- Any `win32com` / `SldWorks.Application` script
- Feature rebuild (extrude/cut/fillet/ref plane) failing or wrong Z
- “SW froze / RPC failed” during agent debug loops
- Chinese GB templates (`GB_Part.prtdot`, `前视基准面`)

## Non-negotiables

1. **Close leftover documents** every iteration. Opening many unnamed parts freezes SW and breaks COM (`RPC 服务器不可用`). Helper pattern: `close_other_docs(swApp)` before/after runs; never leave diag parts open.
2. **API units = metres.** Multiply mm by `0.001`.
3. **Do not sketch on offset planes** via COM — selection looks correct, geometry still lands on Front. Use **Front sketch + extrude thickness + `InsertMoveCopyBody2` Z translate** instead.
4. **Fillet Options must not rely on Propagate alone** — `Options=195` often fillets only one tangent chain. Prefer `Options=2` (uniform) / `0`, **per body**, batch/single-edge fallback.
5. Keep sketches **open**; `FeatureExtrusion2` / `FeatureCut4` consume them. Use `CreateCornerRectangle` only (avoid `CreateArc` Direction bugs).

## Connect + templates

```python
# Prefer GetActiveObject — returns early-bound gen_py when TLB cached.
# EnsureDispatch("SldWorks.Application") often fails on SW 2025:
#   "This COM object can not automate the makepy process"
sw = win32com.client.GetActiveObject("SldWorks.Application")

# One-time TLB wrap (install path may vary):
#   makepy.GenerateFromTypeLibSpec(r"C:\SolidWorks 2025 SP1.1\SOLIDWORKS\sldworks.tlb")
```

- New part: `NewPart()` then known templates under  
  `C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates`  
  (`Part.prtdot` / `零件.prtdot` / `GB_Part.prtdot`). Or `SW_PART_TEMPLATE`.
- `SelectByID2` Callout = `VARIANT(VT_DISPATCH, None)`, never bare `None`.
- `OpenDoc6` / `LoadFile4` errors/warnings: late-bound ByRef Long VARIANTs OK; **early-bound `OpenDoc6` may reject VARIANT ByRef** — rebuild in-process instead of reopen when possible.
- `GetTitle` / `GetActiveSketch2` may be **property or method** depending on binding — guard with `callable(...)`.

## Building boxes at arbitrary Z (the reliable pattern)

Offset `InsertRefPlane` **does** accept signed distance (`flag=4`, `dist=-0.022`) or `flag|8192` flip — but **InsertSketch on that plane still sketches Front**.

**Do this instead:**

1. Select Front / `前视基准面` → sketch rectangle (XY mm)
2. `FeatureExtrusion2` blind, depth=`|zmax-zmin|`, **`Merge=False`** for separate body
3. Select body: `SelectByID2(feat.Name, "SOLIDBODY", ..., mark=1, callout)`
4. `InsertMoveCopyBody2(0, 0, zmin_m, 0, 0,0,0, 0,0,0, False, 0)`
5. Cuts that only hit one region in XY: sketch on Front + **`FeatureCut4` ThroughAll both dirs** (`Sd=False`, `T1=T2=1`)

Verify with `GetPartBox(True)` → divide by `0.001` → expect real Z, not everything stacked on `[0, thickness]`.

## Feature signatures (recorded-macro forms)

| Call | Args to mirror |
|------|----------------|
| `FeatureExtrusion2` | 23-arg macro form; draft angles still `1°` even if draft flags False |
| `FeatureCut4` | 27-arg form |
| `FeatureFillet` | `(Options, R1, Ftyp=0, Overflow=0, None, None, None)` — try Options `2,0,1,193,195` |
| `InsertMoveCopyBody2` | `(tx,ty,tz, dist, rcx,rcy,rcz, rax,ray,raz, copy, nCopies)` — translation in **metres** on tx/ty/tz |

Cut missing solid → `FeatureCut4` returns `None` (wrong Z / wrong Dir / no intersection). Redraw sketch and flip `Dir` rather than assuming one call.

## Fillets

- CadQuery-style: pocket mouth **R0.6**, outer **R1.2** (`L_POCKET_FILLET` / `L_FILLET`).
- Pocket first (edges whose midpoint falls in pocket AABB), then outer per body.
- Edge midpoint/length: use **`edge.GetCurveParams2` as a property** (tuple start+end). Do **not** trust `Evaluate(0.5)` alone (wrong Z seen on SW 2025).
- Skip edges shorter than ~`0.5 * radius` (SW rejects many).
- One Propagate fillet ≠ all edges covered — expect multiple fillet features.

## Multi-body

Move/Copy + `Merge=False` yields multiple solids. `InsertCombineFeature` often returns `None` via COM — leave multibody or join manually in UI. Geometry can still be correct.

## Debug hygiene (agents)

```
Each loop:
1. close_other_docs(swApp)
2. run one experiment OR full create script
3. print GetPartBox mm after each major feature
4. close diag docs — do not pile 零件1..N
```

If COM dies (`-2147023170`): restart SolidWorks, close all docs, retry once.

## Project anchors (EFG wrist)

Reference implementation: `sw/scripts/sw_helper.py`, `create_l_clamp.py`, `dims_*.py`.  
User-facing flow: `用法说明.txt`.

## More detail

- Full pit list and API notes: [pitfalls.md](pitfalls.md)
