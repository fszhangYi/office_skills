# Embody UI style — reference

## Core files

| Path | Role |
| --- | --- |
| `frontend/src/styles/globals.css` | Dark tokens, body font, shared `.page-nav*`, `.pill` |
| `frontend/src/styles/appearance.css` | Light tokens, light overrides, density/`--ui-*` |
| `frontend/src/styles/loading.css` | `.emb-load*` |
| `frontend/src/styles/settings.css` | Settings modal chrome |
| `frontend/src/styles/home.css` / `login.css` | Canonical marketing/login shells |
| `frontend/public/css/ui_motion.css` | Motion tokens, ambience, nav portal polish |
| `frontend/src/main.tsx` | CSS bootstrap + `applyAppearance` |
| `frontend/src/prefs/appearance.ts` | `data-theme` / density (theme skill) |
| `frontend/src/lib/threeTheme.ts` | 3D colors from theme |
| `frontend/src/features/modelAnalysis/chartTheme.ts` | Chart.js from CSS vars |

**Ignore:** `frontend/src/index.css`, `frontend/src/App.css` (unused Vite purple).

## Color tokens

### Dark (`globals.css`)

| Token | Value (approx) |
| --- | --- |
| `--bg` | `#0b1018` |
| `--text` | `#e7ecf3` |
| `--muted` | `#8b9bb4` |
| `--accent` | `#3dd6c6` |
| `--spark` | `#f0b429` |
| `--panel` | `rgba(18,26,38,.9)` |

Also: `--danger` / `--ok` / `--warn` / `--off`, `--surface`–`--surface-3`, `--chrome`, `--input-bg`, `--bg-spot*`, `--brand-title`, header/footer gradient helpers, scrollbar tokens.

### Light (`appearance.css`)

Mirrors the same names with slate/white glass, darker teal `#0f766e`, amber `#b45309`. Defines `--shadow-sm|md|lg|glow` (dark often uses ad-hoc rgba shadows).

## Spacing / density

On `:root` / `html[data-density]`:

| Token | Formula |
| --- | --- |
| `--ui-space` | scale factor |
| `--ui-font-scale` | type scale |
| `--ui-gap` | `calc(16px * var(--ui-space))` |
| `--ui-pad` | `calc(18px * var(--ui-space))` |
| `--ui-header-pad-y` | `calc(14px * …)` (smaller when compact) |

Densities: `comfortable` / `compact` (~0.9) / `dense` (~0.82). Compact flag: `html[data-compact='1']`.

## Motion (`ui_motion.css`)

| Token | Typical |
| --- | --- |
| `--motion-ease` | `cubic-bezier(0.22, 1, 0.36, 1)` |
| `--motion-fast` | 160ms |
| `--motion-med` | 280ms |
| `--motion-slow` | 520ms |
| `--z-page-nav` | `2147483000` |
| `--spark-glow` / `--spark-line` / `--spark-soft` | spark helpers |

## Page CSS inventory

`home`, `login`, `hub`, `chat`, `eval`, `robots`, `pipeline`, `sensors`, `act-pipeline`, `model-analysis`, `dataset-converter`, `pi05-*`, `scoped-pages`.

Convention: root `.{name}-page` scopes legacy/minified rules.

## Shared React chrome

| Component | Classes |
| --- | --- |
| `PageNav` / `PageChrome` | `.page-nav-*` |
| `SettingsModal` / `SettingsGear` | `.settings-*` |
| `PathPickerModal` | `.path-picker-*` |
| Loading overlay | `.emb-load*` |

## Brand checklist for agents

- [ ] Teal + spark both present (not teal-only)
- [ ] Dark bg near `#0b1018`, not pure black or purple
- [ ] Glass panels + thin borders
- [ ] Pill nav / chips
- [ ] IBM Plex (or documented fallback stack including CJK)
- [ ] No leftover Vite indigo theme
