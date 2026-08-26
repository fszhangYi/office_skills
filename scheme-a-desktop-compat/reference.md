# Scheme A 兼容层参考

## 判定检查清单（复制到回复）

```
Scheme A check:
- [ ] frontend: Vite + React + TS
- [ ] backend: FastAPI + requirements
- [ ] agent/SSE or tool orchestration present (or clearly stubbed)
- [ ] can serve SPA from API process (or ready to add)
- [ ] data: SQLite OK for desktop MVP
Verdict: PASS | PARTIAL | FAIL
```

## `paths.py` 行为契约

| 函数 | 冻结态 | 开发态 |
|---|---|---|
| `bundle_dir()` | `_MEIPASS` | `backend/` |
| `user_data_dir()` | OS 用户数据目录/`<app-id>` | 同左 |
| `resolve_frontend_dist()` | `_MEIPASS/frontend-dist` 优先 | `frontend/dist` |
| `ensure_runtime_env()` | 设 env + chdir 用户目录 | 同左 |

`<app-id>` 应用短名（小写、连字符），写入 BUILD_INFO 与文档。

## `desktop_main` 启动顺序（勿打乱）

1. `ensure_runtime_env()`  
2. 重新实例化 `Settings()`（读新 `DATABASE_URL`）  
3. 重建 SQLAlchemy async engine / sessionmaker  
4. `from app.main import app`（此时才 mount 静态资源）  
5. uvicorn 线程 → health → UI  

## Spec 注意点

- **onedir**：`EXE(..., exclude_binaries=True)` + `COLLECT`  
- datas：`(frontend/dist, "frontend-dist")`  
- Windows Wine：精简 `hiddenimports`，避免对 numpy/langchain 做全量 `collect_all`  
- Linux console 可 `True`（便于日志）；Windows 分发可再改 `console=False`  

## 与另外两个 skill 的分工

| Skill | 职责 |
|---|---|
| `scheme-a-desktop-compat` | 校验 + 写兼容代码 |
| `scheme-a-linux-to-linux-desktop` | 在 Linux 上打出 Linux 桌面包 |
| `scheme-a-linux-to-windows-desktop` | 在 Linux 上经 Wine 打出 Windows 桌面包 |
