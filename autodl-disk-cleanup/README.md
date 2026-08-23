# autodl-disk-cleanup

Cursor Agent Skill：在 AutoDL 上诊断系统盘/数据盘空间，安全清理临时文件，并将 conda/venv 等大目录迁移到 `/root/autodl-tmp`。

## Quick start

```bash
# 诊断
python3 scripts/check_disk.py

# 预览
bash scripts/autodl_cleanup.sh --dry-run

# 执行（安全清理 + 迁移 miniconda3 + 已知 venv）
bash scripts/autodl_cleanup.sh --apply
```

日志默认：`/root/autodl-tmp/disk_cleanup.log`

## Install into Cursor

```bash
cp -a autodl-disk-cleanup ~/.cursor/skills/autodl-disk-cleanup
# 或项目级
cp -a autodl-disk-cleanup /path/to/workspace/.cursor/skills/autodl-disk-cleanup
```
