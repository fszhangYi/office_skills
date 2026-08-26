# Linux → Linux（Scheme A）参考

## 产物布局

```
release/<App>-desktop-linux-x64-<utc>/
  AppName                 # ELF 可执行文件
  _internal/              # 依赖 + frontend-dist
  README.txt
  BUILD_INFO.json
release/<App>-desktop-linux-x64-<utc>.tar.gz
release/<App>-desktop-linux-x64-<utc>.zip
```

## BUILD_INFO.json 示例

```json
{
  "product": "my-app",
  "kind": "desktop",
  "platform": "linux-x64",
  "self_contained": true,
  "requires_python_on_target": false,
  "entry": "AppName",
  "built_at_utc": "..."
}
```

## README.txt 要点

- 如何启动：`./AppName`  
- 无需安装 Python/Node  
- 数据目录：`~/.local/share/<app-id>/`  
- 无桌面环境时会开浏览器，关闭终端即停服  

## .gitignore 建议

```
release/
packaging/dist/
packaging/build/
.tools/
.wine-*/
frontend/dist/
backend/.venv/
```

## 与 Windows skill 分工

| 目标 | Skill |
|---|---|
| Linux 包 | `scheme-a-linux-to-linux-desktop` |
| Windows 包（Wine） | `scheme-a-linux-to-windows-desktop` |
| 先改代码 | `scheme-a-desktop-compat` |
