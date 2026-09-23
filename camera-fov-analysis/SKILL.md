---
name: camera-fov-analysis
description: >-
  Geometric camera FOV coverage for wrist/gripper mounts (RealSense D405-style):
  project feature points into camera angles, test in-FOV under stream crop modes
  (16:9 vs 4:3), optional ray occlusion, Markdown report + schematic PNGs.
  Use when the user asks 相机视野分析, FOV 覆盖, 裁切视场, D405 视角, 指尖入画,
  camera-fov-analysis, or to re-analyse after changing lens pose / stream resolution.
---

# camera-fov-analysis — 装配几何视场覆盖

判断固定位姿下的相机（典型：腕部 RealSense D405）能否「看见」指尖/工件特征点。  
**不是**图像标定 / PnP / 内参估计；**是**针孔角域入画 +（可选）射线遮挡。

## When to use

- 改支架位姿、俯角、镜头高度后重算覆盖
- 对比不同 **流分辨率/裁切**（720p vs 640×480）下的图像视场
- 写/更新 `*_FOV_analysis.md` 与示意图 PNG

## Non-goals

- 不估畸变、立体基线、深度精度、曝光/IR
- 不把「分辨率」只当成清晰度（mm/px）；RealSense **档位会改图像 FOV**

---

## Inputs（必须写清）

分析前先从用户或工程脚本冻结下列输入。缺一不可则先补齐再算。

### 1. 坐标系

| 字段 | 说明 |
| --- | --- |
| `frame` | 世界系定义（例：夹爪 STEP，mm，右手；X 开合，Y→指尖，Z 后盖法向） |
| `units` | 默认 `mm` |

### 2. 相机外参（手定/支架脚本，非估出来的）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `LENS` | `(3,)` mm | 镜头中心世界坐标 |
| `look` | 单位向量 | 光轴（指向场景） |
| `right` | 单位向量 | 相机右（通常约 `(-1,0,0)` 或由装配定） |
| `up` | 单位向量 | `normalize(look × right)`；与 `look`、`right` 正交 |
| （可选）`back` | `(3,)` mm | 相机背板中心，仅用于侧视示意图 |

参考实现：`mechanical/wrist_d405/make_bracket.py` 的 `LENS` / `LOOK` / `camera_frame()`。

### 3. 图像视场（随裁切档变化）

| 字段 | 说明 |
| --- | --- |
| `modes[]` | 每个 stream profile 一组 `HFOV_deg`、`VFOV_deg`、名称、宽高比说明 |
| 或本机内参 | `W,H,fx,fy` → `HFOV=2atan(W/(2fx))`，`VFOV=2atan(H/(2fy))` |

**默认档位表（D405 / D400 系，无本机 `-c` 时用）：**

| 模式 id | 典型分辨率 | 宽高比 | 建议 H×V (°) | 来源 |
| --- | --- | --- | --- | --- |
| `HD87` | 1280×720 / 848×480 / 640×360 | 16:9 | **87×58** | 产品页；同比例降采样 ≈ 同 FOV |
| `HD84` | 同上 | 16:9 | **84×58** | 数据手册 D405(D401) HD |
| `VGA80` | 640×480 | 4:3 | **~80×64** | 社区内参估算；以本机为准 |
| `VGA75` | 640×480 | 4:3 | **75×62** | 宽镜头族(D430/D450) 手册 VGA |

D405 手册对 VGA FOV 标 **N/A**；有相机时优先 `rs-enumerate-devices -c`。

### 4. 特征采样点

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `samples[]` | 世界坐标点列表 | 每点：`xyz` + `tag`（如 `blade` / `hook_c` / `hook_o` / `root`） |
| （可选）开合态 | 两套点或同一几何两种 X | 闭合 / 最大开口外撑端 |

由指尖 CAD 参数生成亦可（`FACE*_X`、`JAW_TRAVEL`、`HOOK`、`ZC`、刃长 Y 等）。

### 5. （可选）遮挡网格

| 字段 | 说明 |
| --- | --- |
| `obstacle_stls[]` | 支架 / 外壳 / 后盖 STL |
| 判据 | 射线 `LENS→P` 首交距离 < ‖P−LENS‖ − ε → 遮挡 |

### 6. （可选）报告元数据

标题、装配 STEP 路径、分析日期、相机型号链接。

**输入清单模板（复制给用户确认）：**

```text
[ ] frame + units
[ ] LENS, look, right, up
[ ] FOV modes（或 rs-enumerate-devices -c）
[ ] samples（闭合 + 张开关键点）
[ ] obstacle STLs（若要做遮挡）
[ ] 输出目录
```

示例 JSON 见 [example_config.json](example_config.json)；字段说明见 [reference.md](reference.md)。

---

## Outputs

| 输出 | 内容 |
| --- | --- |
| 每点 `(d, az, el)` | 沿光轴深度 mm；水平角 / 垂直角 ° |
| `in_fov` | `d>1` 且 `|az|≤H/2` 且 `|el|≤V/2`（对该 mode） |
| 汇总表 | 各 mode：入画计数、张开钩裕量、指根是否出画 |
| （可选）遮挡 | clear / blocked + 首交距离 |
| 足迹 | 深度 `d` 处宽×高：`2d tan(H/2)` × `2d tan(V/2)` |
| 报告 MD | 结论、方法、分档表、建议 |
| 图 PNG | 侧视垂直楔 + 角域框；多档叠画；足迹对比 |

**不输出：** `K`、畸变、PnP 位姿、像素坐标、深度图。

---

## Method（固定）

对世界点 `P`：

```text
p = P - LENS
d = p · look
az = atan2(p · right, d)     # rad → deg
el = atan2(p · up, d)
in_fov ⇔ d > 1 mm ∧ |az| ≤ HFOV/2 ∧ |el| ≤ VFOV/2
```

要点：

1. **每个裁切 mode 换一组 H/V**，不要全程死套 87×58  
2. **同 16:9 降采样**（720p→848×480→640×360）≈ 同图像 FOV，只改像素密度  
3. **4:3（640×480）** 通常水平收窄；垂直可能略增  
4. 清晰度（mm/px）是另一层：同一 FOV 下 `2d tan(FOV/2)/N_pixels`

详情与报告结构：[reference.md](reference.md)。

---

## Workflow

```
Task Progress:
- [ ] 1. 冻结 Inputs（坐标系、LENS/轴、modes、samples）
- [ ] 2. 算各点 d,az,el；对每个 mode 判 in_fov + 裕量
- [ ] 3. （可选）射线 vs STL 遮挡
- [ ] 4. 出图：分档侧视+角域、叠画对比、足迹
- [ ] 5. 写 Markdown 报告（结论含「推荐流模式」）
- [ ] 6. 建议：优先 16:9；4:3 须用本机 FOV 复判
```

### 参考工程（EFG-C65 + D405）

| 用途 | 路径 |
| --- | --- |
| 位姿与指尖常量 | `/root/autodl-tmp/mechanical/wrist_d405/make_bracket.py` |
| 多档出图 | `/root/autodl-tmp/mechanical/wrist_d405/make_fov_crop_figures.py` |
| 报告范例 | `/root/autodl-tmp/mechanical/wrist_d405/D405_FOV_analysis.md` |

通用配置驱动脚本（不依赖夹爪工程）：

```bash
python /root/autodl-tmp/office_skills/camera-fov-analysis/scripts/analyze_fov.py \
  /path/to/config.json \
  --out-dir /path/to/out
```

依赖：`numpy`；出图另需 `matplotlib`（CJK 字体如 Noto Sans CJK SC 可选）。

### Agent checklist

1. 先列出 Inputs 表给用户确认，尤其 **FOV modes**  
2. 不要把 640×480 当成「同视野低清」  
3. 报告结论必须写清：哪一档、半角、入画/出画、推荐默认分辨率  
4. 图与 MD 放同一目录；相对路径引用 PNG  

---

## Install into Cursor

```bash
cp -a /root/autodl-tmp/office_skills/camera-fov-analysis \
  ~/.cursor/skills/camera-fov-analysis
# or project-level:
# cp -a ... /path/to/workspace/.cursor/skills/camera-fov-analysis
```
