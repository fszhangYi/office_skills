# SolidWorks 2025 Python COM — pitfalls & tips

Companion to `SKILL.md`. Captured from debugging `create_l_clamp.py` on SW 2025 SP1.1 (rev 33.1.1), Python 3.12, Chinese GB templates.

---

## Environment

| Item | Notes |
|------|--------|
| Install | e.g. `C:\SolidWorks 2025 SP1.1\SOLIDWORKS\SLDWORKS.exe` (not always under Program Files) |
| TLB | `...\SOLIDWORKS\sldworks.tlb` — generate cache: `makepy.GenerateFromTypeLibSpec(tlb_path)` |
| Templates | `C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates` — `GB_Part.prtdot` works |
| Front plane names | `Front Plane`, `前视基准面`, `Front`, `前视`, … |
| pywin32 | Required; scripts should force console UTF-8 (`chcp 65001` / `reconfigure`) |

---

## Binding / makepy

### Pit: `EnsureDispatch("SldWorks.Application")` fails

```
TypeError: This COM object can not automate the makepy process
```

**Tip:** Run makepy once on `sldworks.tlb`. Then `GetActiveObject("SldWorks.Application")` often already returns `win32com.gen_py...SldWorks`. Do not require EnsureDispatch to succeed.

### Pit: App early-bound, PartDoc late-bound

`NewDocument` / `NewPart` may return plain `CDispatch`. Then:

- `CastTo(doc, "PartDoc")` → same makepy error
- `doc.FirstFeature` / `GetNextFeature` / `GetActiveSketch2()` → `找不到成员`
- `GetTitle` may be property (`doc.GetTitle`) not `doc.GetTitle()`

**Tip:** Guard callables; avoid relying on Feature tree walk for logic. Prefer `GetBodies2`, named features, `GetPartBox`.

### Pit: Early-bound `OpenDoc6` + VARIANT ByRef

```
TypeError: int() argument must be ... not 'VARIANT'
```

**Tip:** Prefer building in the same session, or late-bound open. Do not assume `_byref_i4` works with every early-bound signature.

---

## Session / freeze

### Pit: Dozens of open `零件N` windows

Diagnose loops that call `new_part()` without closing → SW UI thrash → COM RPC failure:

```
(-2147023170, '远程过程调用失败。')
```

**Tip:** Always `CloseDoc` extras. Pattern used in production helpers: peel `ActiveDoc` with `close_other_docs(swApp, keep=optional)`.

### Pit: Target STEP locked (`WinError 32`)

Sync/copy into `step\` while SW or Explorer preview has the file open.

**Tip:** Close SW preview of that STP; disable preview pane; retry.

---

## Planes & sketches

### Pit: Offset plane selected (type 4) but solid Z starts at 0

Repro: `InsertRefPlane` at +5.5 mm → select plane → `InsertSketch` / `InsertSketch2` → extrude depth 3.2 → `GetPartBox` Z `[0, 3.2]` not `[5.5, 8.7]`.

Tried: `SelectByID2` with XYZ on plane, `plane.Select2`, `SketchManager.InsertSketch`, `InsertSketch2` — all still Front.

**Tip:** Treat offset-plane sketching as **broken for COM automation** on this stack. Use Front + Move/Copy body.

### Tip: Signed InsertRefPlane works

- `InsertRefPlane(4, -0.02222, 0, 0, 0, 0)` → plane on −Z
- Or `flag = 4 | 8192` with positive distance (flip)

Useful if you ever need a reference face — not for sketch placement.

### Pit: `StartOffset` (T0=3) argument confusion under late binding

Passing `T0=3`, `StartOffset=5.5mm`, `D1=3.2mm` produced Z `[0, 8.7]` (= sum), not `[5.5, 8.7]`. Brute-force T0 also risked leaving many open docs.

**Tip:** Prefer Move/Copy over StartOffset until early-bound Part FeatureManager is proven.

---

## Extrude / cut

### Tip: Keep sketch open

Do not `InsertSketch(False)` before FeatureExtrusion2/Cut4 — they close the sketch.

### Tip: `FeatureExtrusion2` / `FeatureCut4` arity

Match VBA recorded macros (23 / 27 args). Draft angle args still passed as ~1°.

### Pit: `FeatureCut4` returns `None`

Usual causes:

1. No solid intersection (geometry still on wrong Z from abs(offset) bug)
2. Wrong `Dir` / Flip
3. Sketch already consumed by a failed prior call

**Tip:** On failure, exit sketch (`InsertSketch(False)`), recreate sketch, retry opposite `Dir`. For cuts after bodies are placed: **ThroughAll both directions** if XY profile only hits the intended body.

### Tip: ThroughAll cut

```text
FeatureCut4(Sd=False, Flip=False, Dir=False,
            T1=ThroughAll=1, T2=ThroughAll=1, ...)
```

Pocket XY that does not overlap Arm XY will not destroy the arm.

### Tip: Merge flag

Use `Merge=False` when you will `InsertMoveCopyBody2` that body. `Merge=True` only merges bodies that intersect **at creation location** (usually Z≈0 before move).

---

## Move / Copy body

### Tip: Selection mark 1 required

```python
doc.Extension.SelectByID2(feat.Name, "SOLIDBODY", 0, 0, 0, False, 1, null_dispatch, 0)
fm.InsertMoveCopyBody2(0, 0, z_mm * 0.001, 0, 0, 0, 0, 0, 0, 0, False, 0)
```

### Pit: `IBody2.Select2(False, 0)` with early-bound body

Expects `(Append, ISelectData)`, not mark int → `TypeError: cannot be converted to a COM object`.

**Tip:** Use `SelectByID2` SOLIDBODY + mark, or `CreateSelectData` + `Mark=1` when available (CreateSelectData may be missing on late-bound SelectionManager).

### Tip: Proven Z placement

Extrude depth 3.2 at Front → box Z `[0, 3.2]` → Move +5.5 mm → `[5.5, 8.7]`. Negative zmin likewise.

---

## Fillet

### Pit: One FeatureFillet with Options=195

195 includes Propagate — UI may show one “圆角” feature while most edges stay sharp. Multi-body: often only one body chain.

**Tip:**

1. Options try order: `2, 0, 1, 193, 195` (non-propagate first)
2. Always loop **per body**
3. If batch fails → batches of ~8 → single edge
4. Pocket R0.6 **before** outer R1.2, filter edges by midpoint in pocket AABB

### Pit: `Evaluate(0.5)` midpoint wrong

Seen returning absurd Z (e.g. −0.497 m) on a 3 mm tall box.

**Tip:** `edge.GetCurveParams2` is a **property** returning start/end XYZ — use that for midpoint and length.

### Pit: Edges too short for radius

SW silently fails or rejects. Skip length &lt; ~0.5×radius.

---

## Combine / union

### Pit: `InsertCombineFeature` returns None

Tried ops `0,1,2,501–504`, body objects, VARIANT arrays, selection marks — often `None` or type mismatch with `None` args.

**Tip:** Accept multibody for automation; tell user to Combine in UI if a single body is required. Correct bbox still validates design.

---

## SelectByID2 / VARIANT

```python
import pythoncom
from win32com.client import VARIANT
null = VARIANT(pythoncom.VT_DISPATCH, None)
doc.Extension.SelectByID2(name, "PLANE", 0, 0, 0, False, 0, null, 0)
```

Bare `None` for Callout → flaky failures.

---

## Verification checklist

After each boss/cut/move/fillet:

1. `GetPartBox(True)` → mm: X/Y/Z extents match design (not all Z≥0 stacked)
2. Body count (`GetBodies2(0, True)`) — expect multi after several Move/Copy
3. Fillet feature count ≫ 1 if many edges (or per-body names)
4. No extra documents left open

Expected L-clamp envelope (plate-local mm), approx:

- X `[-39.5, 6]`, Y `[-14, 14]`, Z `[-22.22, 8.70]`

---

## Anti-patterns (do not repeat)

1. `insert_offset_plane(..., abs(z))` for negative Z — pads/pockets end up on +Z
2. Debug loops without closing parts
3. Assuming offset-plane sketch = offset-plane geometry
4. One Propagate fillet for “all edges”
5. `CreateArc` in rebuild scripts without testing Direction on this SW build
6. Trusting StartOffset without GetPartBox proof
7. Leaving STEP files open while syncing `step\`

---

## Quick recipe — axis-aligned box at [x0,x1]×[y0,y1]×[z0,z1] mm

```text
select Front → InsertSketch
CreateCornerRectangle(x0,y0,x1,y1) in metres
FeatureExtrusion2 blind depth=|z1-z0|, Merge=False, name feature
SelectByID2(name, SOLIDBODY, mark=1)
InsertMoveCopyBody2(0,0,min(z0,z1)*0.001, ...)
clear selection
```

Cuts: Front rectangle + FeatureCut4 ThroughAll both ways when safe in XY.
