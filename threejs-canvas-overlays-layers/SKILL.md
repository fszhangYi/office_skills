---
name: threejs-canvas-overlays-layers
description: >-
  Port rs-detect-style Three.js canvas enhancements: camera CAD overlays with
  per-camera color/XYZ/RPY, ± nudge + configurable step, Ctrl+↑↓ zoom-to-cursor,
  persisted default poses, model layer show/hide panel, draw primitives
  (box/sphere/cylinder) with editable layers, camera-group visibility ref fix,
  and wider side panel. Use when the user asks to strengthen a Three.js arm /
  robot / scene canvas with overlays, layers, nudges, or cursor zoom — especially
  ROS Z-up + Rx(-90°) apps like rs-detect / sensors-arm Cell C.
---

# threejs-canvas-overlays-layers

把 **rs-detect Arm 画布**（2026-11-15）里验证过的 8 项加强，迁移到其它 Three.js 应用。

Canonical 实现：

| 件 | 路径 |
| --- | --- |
| React 画布 | `rs-detect/web/src/components/ArmPanel.jsx` |
| 样式 | `rs-detect/web/src/styles.css` |
| API | `rs-detect/src/rs_detect/api/server.py`（`/api/camera_overlays`、`/api/draw_shapes`） |
| 配置 | `rs-detect/config/camera_overlays.yaml`、`draw_shapes.yaml` |
| 摘录 | 本 skill [`reference/`](reference/) |

源码摘录索引见 [reference/INDEX.md](reference/INDEX.md)。

## When to use

- 机械臂 / 工位 Three.js 画布需要 **CAD 叠加对齐**（相机、夹具、工装）
- 需要 **毫米级微调**：滑条 + `±` + 可配置 step
- 需要 **以鼠标为中心缩放**（键盘 Ctrl+↑↓，不卡死）
- 需要 **按文件来源分层显隐**（URDF / 场景 STL / 相机组 / 绘制）
- 需要 **可编辑绘制体**（长方体 / 球 / 圆柱）并持久化

## Non-goals

- 不做真 CSG / 布尔网格运算（rs-detect 曾试过，已撤销）
- 不替代手眼标定求解；此处只是 **可视化对齐与编辑**
- 不强制 URDF；可只接 STL / 自定义 Object3D

---

## 坐标系约定（所有叠加共用）

ROS / 机器人 **Z-up、米制** 位姿，进 Three.js（Y-up）前统一左乘：

\[
M = R_x(-90^\circ)\, T(\mathrm{offset\_m})\, R_{\mathrm{XYZ}}(\mathrm{offset\_rpy\_deg})\, [S]
\]

- Euler 顺序与 Three.js 一致：`Euler(rx, ry, rz, "XYZ")`（**本征 / intrinsic XYZ**）
- 相机 STL 若单位是 mm，再乘 `S = scale`（常见 `0.001`）
- 场景 CAD 若另有底座对齐，在 `T/R` 之外再插 `align` 矩阵（rs-detect scene overlay 另有 `base_in_scene_mm` + yaw）

**移植时先统一这一条**，否则滑条数值与示教器 / YAML 对不上。

---

## 功能总览（前八项）

| # | 功能 | 用户价值 | 关键文件 / 摘录 |
| --- | --- | --- | --- |
| 1 | 相机 CAD 叠加 | D435/D405 等官方 STL，分色、逐个 XYZ/RPY、保存 | `05_cam_matrix_and_apply.js`、`09_camera_overlays.example.yaml` |
| 2 | `±` 微调 + step | 滑条粗调，按钮按 step 精调；XYZ/RPY step 可改 | `01_nudge_slider_and_step.js`、`08_styles_*.css` |
| 3 | Ctrl+↑↓ 缩放 | 以当前鼠标为中心缩放；防 key-repeat 卡死 | `07_orbit_zoom_to_cursor.js` |
| 4 | 默认位姿 | 调好的 `offset_m` / `offset_rpy_deg` 写入 YAML 默认 | `09_camera_overlays.example.yaml` |
| 5 | 模型图层面板 | 按来源文件分层，开关只改显示 | `04_layer_rows.js`、`03_layer_visibility_*.js` |
| 6 | 绘制图元 | 长方体/球/圆柱；独立层；同套 XYZ/RPY | `02_draw_shape_*.js`、`06_shape_matrix_*.js` |
| 7 | 相机组显隐修复 | 组隐藏后再开，不被过期 `visible=false` 盖掉 | `03_layer_visibility_and_cam_group.js` |
| 8 | 面板加宽 | 侧栏约 360px（原 240 的 1.5×） | `08_styles_nudge_and_panel.css` |

---

## 1. 相机 CAD 叠加

### 行为

- 配置里列出多台相机：`id`、`label`、`url`（STL）、`color`、`offset_m`、`offset_rpy_deg`、`scale` / `units_of_file`
- 画布上 `THREE.Group`（`camera_overlays`）挂所有 mesh；`mesh.name = cam.id`
- UI：下拉选中一台 → 滑条/± 改位姿 →「保存」→ `PUT /api/camera_overlays`
- **颜色区分**机械臂灰 / 场景青灰，便于扫一眼认型号

### 矩阵（必抄）

见 [reference/05_cam_matrix_and_apply.js](reference/05_cam_matrix_and_apply.js)：

```js
// M = Rx(-90°) * T(offset_m) * R_XYZ(rpy_deg) * S(scale)
```

应用时：

```js
child.matrixAutoUpdate = false;
child.matrix.copy(buildCamMatrix(cam));
child.updateMatrixWorld(true);
```

### 几何缓存

同一 `url` 只 `STLLoader` 一次，挂 `__rsShared`，dispose 时跳过共享 `BufferGeometry`，避免反复开关图层把几何 dispose 掉。

### API / YAML

- `GET/PUT /api/camera_overlays` → `config/camera_overlays.yaml`
- 示例字段见 [reference/09_camera_overlays.example.yaml](reference/09_camera_overlays.example.yaml)

### 移植清单

```text
- [ ] cameras[] YAML + GET/PUT
- [ ] Group camera_overlays + per-cam mesh.name
- [ ] buildCamMatrix 与机器人同一 Rx(-90°)
- [ ] 选中高亮（opacity↑ + emissive）
- [ ] 共享 STL 缓存与安全 dispose
```

---

## 2. `±` 微调 + 可配置 step

### 行为

- 每一轴：`[label | Slider | − + | 数值]`
- 上方：`XYZ step (m)`、`RPY step (°)` 两个 `InputNumber`
- `−`/`+` 按 **当前 step** 加减，并 `clamp` 到 `[min,max]`，再对齐到 step 网格（避免浮点漂移）

### 实现要点

见 [reference/01_nudge_slider_and_step.js](reference/01_nudge_slider_and_step.js)：

- `clampRound(v, min, max, step)`：先夹紧，再 `round(v/step)*step`，再夹紧，`toFixed` 控制位数
- `NudgeSliderRow`：Slider 与 Button 共用 `setClamped`
- `StepControls`：改 step 只影响后续 ± / Slider 的 `step` 属性

### CSS

见 [reference/08_styles_nudge_and_panel.css](reference/08_styles_nudge_and_panel.css)：

- `.arm-joint-row.with-nudge`：`grid-template-columns: 36px 1fr auto 64px`
- `.arm-joint-nudge`：窄按钮 22×22

### 移植清单

```text
- [ ] clampRound
- [ ] NudgeSliderRow + StepControls
- [ ] 相机 / 场景 / 绘制 三处复用同一组件
- [ ] XYZ 用米、RPY 用度；显示 digits 随 step 自适应
```

---

## 3. Ctrl+↑↓ 以鼠标为中心缩放

### 行为

- `OrbitControls.zoomToCursor = true`（滚轮已按光标缩放）
- **Ctrl（或 Meta）+ ArrowUp/Down**：在指针位置合成 `WheelEvent`
- 输入框内不拦截（避免改数字时误缩放）

### 防卡死（重要）

直接在 `keydown` 里同步 `dispatchEvent(wheel)` + key-repeat 会把主线程打满 → **画布卡死**。

正确做法见 [reference/07_orbit_zoom_to_cursor.js](reference/07_orbit_zoom_to_cursor.js)：

1. `pointermove` / `pointerleave` 记录指针 client 坐标
2. keydown 只累加 `zoomDeltaY`，`preventDefault`
3. `requestAnimationFrame` **每帧最多派发一次** wheel
4. cleanup 卸监听 + cancel rAF

```js
controls.zoomToCursor = true;
zoomDeltaY += e.code === "ArrowUp" ? -80 : 80; // Up = 放大
if (!zoomRaf) zoomRaf = requestAnimationFrame(flushKeyZoom);
```

### 移植清单

```text
- [ ] controls.zoomToCursor = true
- [ ] pointer 跟踪 + keydown 累加 delta
- [ ] rAF 合并；INPUT/TEXTAREA 跳过
- [ ] unmount cleanup
```

---

## 4. 默认位姿写入配置

### 行为

人工（或算法）调到满意后，把 `offset_m` / `offset_rpy_deg` 写成 YAML 默认值；下次加载 API 直接恢复。

rs-detect 例（D405·A）：

```yaml
offset_m: [0.434, 0.162, 0.414]
offset_rpy_deg: [-174.0, -33.5, 96.0]
```

可选元数据：`seed_med_mm`、`align_method`、`refine_metrics`（方便以后对比精调前后）。

### 移植清单

```text
- [ ] 保存 API 写回同一 YAML（不要只改 React state）
- [ ] 文档注明 Euler 是 Three.js XYZ，避免与 ROS RPY 约定混淆
- [ ] 大改默认前先备份旧 YAML
```

---

## 5. 模型图层面板

### 行为

画布右上角可收起面板「模型图层」：每一行 = 一个显示源（文件名 + 色块 + Switch）。

典型行：

| id | 含义 |
| --- | --- |
| `robot` | 实体 URDF |
| `ghost` | 半透明预览臂 |
| `scene` | 场景 STL |
| `cam_group` / `cam:<id>` | 相机组 / 单相机 |
| `draw_group` / `draw_layer:*` / `draw_shape:*` | 绘制树 |
| `tcp` / `markers` | 标记 |

**开关默认只改显示，不自动写配置**（相机/绘制若业务需要持久化，走各自「保存」按钮）。

### 实现

- `layerRows` 纯函数从 state 拼表：见 [reference/04_layer_rows.js](reference/04_layer_rows.js)
- `setLayerVisible(id, on)` 分派到各 setter：见 [reference/03_layer_visibility_and_cam_group.js](reference/03_layer_visibility_and_cam_group.js)
- UI：`arm-canvas-side-stack` → `arm-layers-panel`（宽约 **360px**）

### 移植清单

```text
- [ ] layerRows 数据驱动（indent 表示父子）
- [ ] setLayerVisible 路由表
- [ ] 未加载项 Switch disabled（ghost 除外）
- [ ] 收起时只留标题条
```

---

## 6. 绘制：长方体 / 球 / 圆柱

### 行为

- 侧栏「绘制」：新建层、新建图元、改尺寸/颜色、XYZ/RPY、保存
- 图元类型：`box`（长方体）、`sphere`、`cylinder`
- 坐标系与相机相同：`Rx(-90°) * T * R`
- 圆柱：Three 默认 Y 轴高 → `geometry.rotateX(π/2)`，使高度沿 ROS Z（再经 Rx(-90°) 进 Three）

### 默认与几何

见 [reference/02_draw_shape_defaults_geom.js](reference/02_draw_shape_defaults_geom.js)。

### 矩阵与应用

见 [reference/06_shape_matrix_and_apply.js](reference/06_shape_matrix_and_apply.js)（无 scale，米制直接建模）。

### 数据模型

```yaml
enabled: true
active_layer_id: layer_1
layers:
  - id: layer_1
    label: 绘制层 1
    enabled: true
    shapes:
      - id: box_xxx
        type: box          # box | sphere | cylinder
        size_m: [0.1, 0.08, 0.05]   # box
        # radius_m / height_m      # sphere / cylinder
        offset_m: [0.4, 0, 0.35]
        offset_rpy_deg: [0, 0, 0]
        color: '#5b8ff9'
        opacity: 0.55
        enabled: true
```

API：`GET/PUT /api/draw_shapes`。

### 移植清单

```text
- [ ] layers[] + shapes[] CRUD
- [ ] makeShapeGeometry + buildShapeMatrix
- [ ] 改尺寸要 rebuild geometry；改位姿只改 matrix
- [ ] 图层树同步进「模型图层」面板
```

---

## 7. 相机组隐藏后再显示（大坑）

### 症状

图层里关掉「相机组」再打开：组仍不可见，或闪一下又没了。

### 根因

`applyCamMatrices` 里若写：

```js
group.visible = !!cfg.enabled && camOverlayVisible; // camOverlayVisible 来自闭包/state，可能过期
```

在「刚 setState(true)」同一次调用里，**state 仍是 false**，把 `visible` 又盖回 false。

### 修法

1. 专用 `camOverlayVisibleRef`（同步），与 React state 双写  
2. `applyCamMatrices(cfg, selectedId, { visible })`：优先用显式 `opts.visible`，否则读 **ref**  
3. `setCamGroupShown(true)`：先写 ref，再 `applyCamMatrices(..., { visible: true })` 或重新 `loadCameraOverlays`

见 [reference/03_layer_visibility_and_cam_group.js](reference/03_layer_visibility_and_cam_group.js) 与 `05_cam_matrix_and_apply.js` 中的 `opts.visible` / `camOverlayVisibleRef`。

绘制组用同样模式（`drawVisibleRef`）。

### 移植清单

```text
- [ ] 凡「UI 显隐 + 异步 apply」都用 ref，不要只信 setState 后立刻读 state
- [ ] apply* 支持 opts.visible 覆盖
- [ ] 回归：关组 → 开组 → 单相机开关 → 保存再刷新
```

---

## 8. 侧栏加宽

### 行为

图层面板宽度 **240 → 360**（+50%），方便看文件名与布尔/规则（若有）。

### CSS

```css
.arm-layers-panel { width: 360px; /* was 240 */ }
.arm-canvas-side-stack {
  position: absolute; top: 48px; right: 12px;
  display: flex; flex-direction: column; align-items: flex-end;
  pointer-events: none; /* 子面板 pointer-events: auto */
}
```

见 [reference/08_styles_nudge_and_panel.css](reference/08_styles_nudge_and_panel.css)。

---

## 推荐落地顺序

```text
1. 坐标系 Rx(-90°) + 一个 STL overlay 跑通
2. NudgeSliderRow + StepControls
3. camera_overlays YAML/API + 分色
4. camOverlayVisibleRef 显隐修复
5. OrbitControls zoomToCursor + Ctrl 缩放（带 rAF）
6. 模型图层面板 layerRows
7. draw_shapes 长方体/球/圆柱
8. 面板宽度与文案打磨
```

## 验收（抄到目标项目）

```text
- [ ] 改相机 XYZ 1mm（step=0.001）画面同步动
- [ ] ± 与滑条同一数值；刷新后 YAML 恢复
- [ ] Ctrl+↑ 以鼠标处放大；按住不卡死
- [ ] 相机组关→开，mesh 可见
- [ ] 模型图层可单独关 URDF / 场景 / 某相机
- [ ] 新建长方体，改 RPY，保存再开仍在
- [ ] 侧栏约 360px，长文件名可读
```

## 与其它 skill 的边界

| 需求 | 用哪个 |
| --- | --- |
| 腕部相机几何 FOV 能否看见指尖 | `camera-fov-analysis` |
| sensors-view iframe 嵌入 | `sensors-view-iframe-embed` |
| 本画布叠加 / 图层 / 微调 / 缩放 | **本 skill** |
