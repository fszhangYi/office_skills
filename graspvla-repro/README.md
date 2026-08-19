# graspvla-repro

Cursor Agent Skill：在本机复现 GraspVLA（Model Server + `offline_test`，端口 6006）。

逐步命令与踩坑以 [GraspVLA_手把手复现教程.md](GraspVLA_手把手复现教程.md) 为 ref。

## 硬门禁

开始任何安装/下载/serve 之前：

```bash
python3 scripts/check_prereqs.py --phase all      # 从零到验收
python3 scripts/check_prereqs.py --phase download # 无 GPU 只拉权重
python3 scripts/check_prereqs.py --phase serve    # 要 CUDA / 10GB 显存
```

不通过时打印 `Exit reasons` 并以 exit code 1 退出。Agent 必须停止。

## 安装到 Cursor

```bash
cp -a graspvla-repro /path/to/workspace/.cursor/skills/graspvla-repro
# 或
cp -a graspvla-repro ~/.cursor/skills/graspvla-repro
```
