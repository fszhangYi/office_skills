# Reference index — threejs-canvas-overlays-layers

摘录自 **rs-detect**（2026-11-15）`web/src/components/ArmPanel.jsx` / `styles.css` / `config/camera_overlays.yaml`。  
行号会漂移；以符号与注释为准，对照当前仓库。

| 文件 | 对应功能 | 内容 |
| --- | --- | --- |
| [01_nudge_slider_and_step.js](01_nudge_slider_and_step.js) | #2 ± 与 step | `NudgeSliderRow`、`StepControls`（依赖同文件的 `clampRound`） |
| [02_draw_shape_defaults_geom.js](02_draw_shape_defaults_geom.js) | #6 绘制 | `defaultDrawShape`、`makeShapeGeometry`（长方体/球/圆柱） |
| [03_layer_visibility_and_cam_group.js](03_layer_visibility_and_cam_group.js) | #5 #7 | `setCamGroupShown`、`setLayerVisible`、draw 显隐；**ref 修复** |
| [04_layer_rows.js](04_layer_rows.js) | #5 | `layerRows` 表：robot/ghost/scene/cam/draw/tcp/markers |
| [05_cam_matrix_and_apply.js](05_cam_matrix_and_apply.js) | #1 #7 | `buildCamMatrix`、`applyCamMatrices`（`opts.visible` + ref） |
| [06_shape_matrix_and_apply.js](06_shape_matrix_and_apply.js) | #6 | `buildShapeMatrix`、`applyDrawShapes` |
| [07_orbit_zoom_to_cursor.js](07_orbit_zoom_to_cursor.js) | #3 | `zoomToCursor` + Ctrl+↑↓ + **rAF 合并防卡死** |
| [08_styles_nudge_and_panel.css](08_styles_nudge_and_panel.css) | #2 #8 | nudge 栅格、side-stack、面板 **360px** |
| [09_camera_overlays.example.yaml](09_camera_overlays.example.yaml) | #1 #4 | D435/D405 分色与默认位姿示例 |

## 完整源路径（工作区）

```text
rs-detect/web/src/components/ArmPanel.jsx
rs-detect/web/src/styles.css
rs-detect/config/camera_overlays.yaml
rs-detect/config/draw_shapes.yaml
rs-detect/src/rs_detect/api/server.py   # /api/camera_overlays, /api/draw_shapes
rs-detect/src/rs_detect/paths.py        # CAMERA_OVERLAYS_PATH, DRAW_SHAPES_PATH
```

## 注意

- 摘录中的 `clampRound`、`api`、`message`、`THREE` 等依赖原组件作用域；移植时一并带上或改成目标项目等价物。
- `07_orbit_zoom_to_cursor.js` 截取自 `useEffect` 内初始化片段，需放进 canvas mount 生命周期并在 cleanup 调用 `_zoomCleanup`。
