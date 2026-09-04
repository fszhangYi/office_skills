---
name: add-favicon
description: >-
  Add brand favicon/app icons for FastAPI HTML shells and PyInstaller desktop
  packages: SVG+PNG+ICO under static assets, HTML link tags, /favicon.ico route,
  auth public paths, EXE icon=. Use when adding favicon, app icon, .ico, desktop
  exe icon, apple-touch-icon, or branding browser tab / packaged Windows build.
---

# Add favicon (web + desktop)

Reference implementation: `sensors-dcs` (2026-09-04). Also mirrors embody /
sensors-view asset set (`favicon.svg` + `.ico` + `.png`).

## Goal

One brand mark for:

1. **Browser tab** (dev + packaged UI opened in Edge/Chrome/pywebview)
2. **Login / header chrome** (optional `<img>`)
3. **Windows `.exe` file icon** (PyInstaller `EXE(..., icon=…)`)

Do **not** rely on Google Fonts / CDN for icons. Ship files next to the app.

## Asset set (required)

Put under the package static dir (example: `src/<pkg>/static/`):

| File | Role |
| --- | --- |
| `favicon.svg` | Primary (sharp at any DPI); brand colors |
| `favicon.png` | 64×64 (or 180×180) apple-touch / fallback |
| `favicon.ico` | Multi-size (16/32/48/64/128/256) for `/favicon.ico` + PyInstaller |

### Generate ICO/PNG from a drawn mark

Pillow is enough (no need for cairosvg):

```python
from PIL import Image, ImageDraw
# render(size) -> RGBA Image matching the SVG geometry
big = render(256)
big.save("favicon.ico", format="ICO",
         sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
render(64).save("favicon.png")
```

Verify: `file favicon.ico` should say **N icons** (N≥4), not a single 16×16.

Brand tip for teal/spark lab UIs: dark rounded square `#121a26`, accent ring
`#3dd6c6`, spark center `#f0b429` (same tokens as embody / sensors-dcs).

## Web wiring checklist

```text
- [ ] 1. Assets in static/ (bundled by package data / PyInstaller datas)
- [ ] 2. Serve static at /assets (StaticFiles) — already common
- [ ] 3. In every HTML shell <head>:
        <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml" />
        <link rel="icon" href="/assets/favicon.ico" sizes="any" />
        <link rel="apple-touch-icon" href="/assets/favicon.png" />
- [ ] 4. Explicit GET /favicon.ico → FileResponse(static/favicon.ico)
        (browsers probe this path even when <link> exists)
- [ ] 5. Auth allowlist: PUBLIC_EXACT includes "/favicon.ico";
        "/assets/" prefix already covers svg/png/ico
- [ ] 6. Optional UI: login logo + header mark use /assets/favicon.svg
- [ ] 7. Tests: assets exist; /favicon.ico and /assets/favicon.* return 200;
        login HTML contains rel="icon"
```

FastAPI sketch:

```python
@app.get("/favicon.ico")
async def favicon_ico():
    from fastapi.responses import FileResponse
    ico = static_root() / "favicon.ico"
    return FileResponse(ico, media_type="image/x-icon")
```

Vite/React SPAs: put the same trio in `public/` or `frontend/public/` and keep
the same `<link>` tags in `index.html` (embody pattern).

## Desktop (PyInstaller) checklist

```text
- [ ] 1. datas already copies static/ into the onedir bundle
- [ ] 2. EXE(..., icon=str(static / "favicon.ico")) when file exists
- [ ] 3. Rebuild Windows package; confirm .exe icon in Explorer
- [ ] 4. pywebview: many builds have no create_window(icon=…);
        tab/window chrome still picks up HTML favicon — that is enough
```

Spec fragment:

```python
_icon = SRC / "pkg" / "static" / "favicon.ico"
exe = EXE(..., icon=str(_icon) if _icon.is_file() else None)
```

## Pitfalls

- **ICO with 1 size** — Pillow `append_images` can silently under-emit; prefer
  one large image + `sizes=[…]`.
- **Auth gate blocks `/favicon.ico`** — tab stays default globe; add public path.
- **Only SVG** — Windows EXE and older browsers want `.ico`.
- **Icon only on EXE, not in HTML** — browser/webview tab still blank.
- **CDN favicon** — breaks offline / Wine / air-gapped lab machines.

## Port targets

| Stack | Where |
| --- | --- |
| FastAPI HTML shell | `viz.py` / `login_page.py` + `static/` |
| React+Vite | `frontend/index.html` + `public/favicon.*` |
| Scheme A Windows | `*-desktop-win.spec` → `EXE(icon=…)` |

Companions: `embody-ui-style` (colors), `embody-login-page` (login mark),
`scheme-a-linux-to-windows-desktop` (spec / Wine build).

Details & sensors-dcs map: [reference.md](reference.md).
