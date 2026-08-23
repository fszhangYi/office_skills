# AutoDL 磁盘清理 — 参考

## 典型案例（2026-08）

系统盘 30G 100% 满，根因：

| 路径 | 大小 | 处理 |
| --- | --- | --- |
| `/root/miniconda3` | 25G | `mv` → `/root/autodl-tmp/miniconda3`，软链回 `/root/miniconda3` |
| `/root/GraspVLA_env` | 6.8G | 同上 |
| `/tmp/convert_workers_test` + `*.hdf5` | 3.7G | 直接删除 |
| `/var/cache/apt` | ~45M | `apt-get clean` |

结果：overlay 从 **100% → 5%**（可用 ~29G）。

## 阈值建议

| 指标 | 建议 |
| --- | --- |
| `/` 可用 | 装 conda 包 / pip 大依赖前保持 **≥ 8 GiB** |
| `/root/autodl-tmp` 可用 | 下载 checkpoint 前 **≥ 20 GiB** |
| `/tmp` 单文件 | `*.hdf5` > 100M 且 mtime > 7 天可列为候选删除 |

## 判断是否已在数据盘

```bash
df -h /root/miniconda3 /root/autodl-tmp
readlink -f /root/miniconda3
```

若 `readlink` 指向 `/root/autodl-tmp/...`，说明已迁移。

## 软链迁移模板

```bash
SRC=/root/miniconda3
DEST=/root/autodl-tmp/miniconda3
[ -L "$SRC" ] && echo "already symlink" && exit 0
[ ! -d "$SRC" ] && echo "missing" && exit 1
mv "$SRC" "$DEST"
ln -s "$DEST" "$SRC"
```

## 与 graspvla-repro 的关系

`graspvla-repro` 的 `check_prereqs.py` 会在安装前检查磁盘；本 skill 用于**已经满了**或用户主动要求清理时释放空间。清理后可用 `check_prereqs.py` 复验。
