# camera-fov-analysis — reference

## Projection formulas

World point \(P\), lens \(L\), orthonormal camera axes \(\hat{\ell},\hat{r},\hat{u}\):

\[
\mathbf{p}=P-L,\quad
d=\mathbf{p}\cdot\hat{\ell},\quad
\mathrm{az}=\mathrm{atan2}(\mathbf{p}\cdot\hat{r},\,d),\quad
\mathrm{el}=\mathrm{atan2}(\mathbf{p}\cdot\hat{u},\,d)
\]

In FOV (degrees): \(d>1\) and \(|\mathrm{az}|\le H/2\), \(|\mathrm{el}|\le V/2\).

From intrinsics:

\[
H=2\arctan\frac{W}{2f_x},\qquad
V=2\arctan\frac{H_{\mathrm{img}}}{2f_y}
\]

Footprint at depth \(d\):

\[
W_{\mathrm{mm}}=2d\tan(H/2),\qquad
H_{\mathrm{mm}}=2d\tan(V/2)
\]

Ground sample (same FOV): \(\mathrm{mm/px}\approx W_{\mathrm{mm}}/W_{\mathrm{px}}\).

## RealSense crop vs FOV

Datasheet §4.3 (D400 family): FOV changes with resolution and aspect ratio. HD is 16:9; VGA is 4:3.

| Aspect | Typical streams | Image FOV behaviour |
| --- | --- | --- |
| 16:9 | 1280×720, 848×480, 640×360, … | Same image FOV; density changes |
| 4:3 | 640×480 | Different crop; usually **narrower HFOV** |

Read per-profile FOV: `rs-enumerate-devices -c`.

D405 (module D401) handbook typical HD: **84°×58°**; product page often **87°×58°**; VGA FOV listed **N/A** — use device or sibling wide VGA **75°×62°** as reference only.

## Side-view vertical wedge

Rotate `look` about `right` by \(\pm V/2\) to get upper/lower rays; draw in YZ (or the plane containing `look` and `up`).

## Occlusion (optional)

Ray from `LENS` toward sample; intersect obstacle meshes (trimesh). Blocked if first hit distance < target distance − ε (e.g. 1 mm).

## Report skeleton

```markdown
# … 相机视野分析报告

## 0. 示意图
## 1. 结论摘要   # 含推荐流分辨率
## 2. 结构与相机位姿
## 3. 分析方法
### 3.1 裁切与图像视场
## 4. 视场覆盖结果
### 4.x 分档裁切对比 + 图
## 5. 与设计目标对照
## 6. 风险与边界
## 7. 建议
## 8. 依据文件
```

## EFG-C65 + D405 defaults (reference only)

| Item | Value |
| --- | --- |
| LENS | (−6.93, 50, 210) mm |
| look | (0, 0.707, −0.707) — 45° down from +Y |
| right | (−1, 0, 0) |
| Product FOV | 87°×58° |
| Datasheet HD | 84°×58° |
| Tip work depth | ~90–120 mm along look |
