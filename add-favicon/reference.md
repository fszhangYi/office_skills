# add-favicon — reference

## sensors-dcs map (canonical port)

| Piece | Path |
| --- | --- |
| Assets | `src/sensors_dcs/static/favicon.{svg,png,ico}` |
| Static root helper | `src/sensors_dcs/static_assets.py` |
| HTML `<link>` | `viz.py` `PREVIEW_HTML` `<head>`, `login_page.py` `<head>` |
| Login / header `<img>` | `login_page.py` `.login-logo`, `viz.py` `.header-logo` |
| `/favicon.ico` route | `viz.py` `create_viz_app` |
| Auth public | `auth_session.py` `PUBLIC_EXACT` → `"/favicon.ico"` |
| PyInstaller icon | `packaging/sensors-dcs-desktop-win.spec` → `EXE(icon=…)` |
| datas bundle | same spec: `(…/static, "sensors_dcs/static")` |
| Tests | `tests/test_favicon_routes.py` |

## embody / sensors-view parallels

| Project | Assets | HTML |
| --- | --- | --- |
| embody_model_eval | `assets/favicon.*`, `frontend/public/favicon.svg` | `frontend/index.html` triple `<link>` |
| sensors-view | `app/static/assets/favicon.svg` | `templates/index.html`, `login.html` |

## HTML snippet (copy)

```html
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml" />
<link rel="icon" href="/assets/favicon.ico" sizes="any" />
<link rel="apple-touch-icon" href="/assets/favicon.png" />
```

Adjust href prefix if static mount is `/static/assets` (sensors-view) instead of `/assets`.

## Minimal SVG template (64×64)

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <rect width="64" height="64" rx="14" fill="#121a26"/>
  <circle cx="32" cy="32" r="14" stroke="#3dd6c6" stroke-width="3"/>
  <circle cx="32" cy="32" r="5" fill="#f0b429"/>
  <path d="M32 10v8M32 46v8M10 32h8M46 32h8" stroke="#3dd6c6" stroke-width="2.5" stroke-linecap="round"/>
</svg>
```

Redraw geometry in Pillow when producing PNG/ICO so raster matches SVG.

## Install

```bash
cp -a add-favicon ~/.cursor/skills/add-favicon
# or project-level:
cp -a add-favicon /path/to/workspace/.cursor/skills/add-favicon
```
