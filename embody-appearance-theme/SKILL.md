---
name: embody-appearance-theme
description: >-
  Port Embody Model Eval light/dark appearance plumbing: ThemePref
  (system|dark|light), density/compact, applyAppearance on
  html[data-theme|data-density|data-compact], localStorage embody.*,
  AppearanceProvider, pre-React FOUC boot, chartTheme/threeTheme consumers.
  Use when adding a theme toggle, prefers-color-scheme, settings appearance
  panel, data-theme CSS switch, or porting theme prefs to another React+Vite
  app that already has CSS variables. Defer visual identity to embody-ui-style.
---

# Embody appearance theme

Canonical: `/root/autodl-tmp/embody_model_eval/frontend/src/prefs/appearance.ts`,
`AppearanceContext.tsx`, `styles/globals.css`, `styles/appearance.css`.

Visual identity (teal/spark look) → `embody-ui-style`. This skill is **prefs → DOM attrs → CSS/canvas**.

## Architecture

```text
localStorage (embody.theme | compact | density)
  → readStoredAppearance / persistAppearance
  → resolveTheme(system → prefers-color-scheme)
  → applyAppearance → <html>
       data-theme="dark|light"        # resolved — CSS + Three/Chart
       data-theme-pref="system|…"     # raw pref (not used by CSS)
       data-compact="0|1"
       data-density="comfortable|compact|dense"
       style.colorScheme = resolved
  → globals.css dark tokens on :root
  → appearance.css light overrides + density
  → Chart.js / Three.js bridge modules
```

Dark-first: `:root` already carries dark tokens (matches default `theme: 'dark'`).

## Port checklist

```text
- [ ] 1. Copy appearance.ts + AppearanceContext.tsx; namespace storage keys
- [ ] 2. main.tsx: after CSS import, applyAppearance(readStoredAppearance()) before createRoot
- [ ] 3. Wrap app with AppearanceProvider
- [ ] 4. Dark (or default) tokens on :root; opposite theme under html[data-theme=…]
- [ ] 5. Optional density/compact if --ui-space / --ui-pad exist
- [ ] 6. Settings: System / Dark / Light (+ compact/density)
- [ ] 7. Charts: getComputedStyle after theme change; Canvas: MutationObserver on data-theme
- [ ] 8. Optional stronger FOUC: inline <head> script (source app skips this)
```

If the target app already uses CSS vars consistently, **only reassign vars** under `html[data-theme='light']` — do not copy the whole light override soup.

## API

```ts
ThemePref = 'system' | 'dark' | 'light'
DensityPref = 'comfortable' | 'compact' | 'dense'
DEFAULT_APPEARANCE = { theme: 'dark', compact: false, density: 'comfortable' }

readStoredAppearance() / persistAppearance(prefs)
resolveTheme(pref) → 'dark' | 'light'
applyAppearance(prefs) → resolved theme

useAppearance() → {
  theme, compact, density,
  setTheme, setCompact, setDensity,
  resolvedTheme,
}
```

### Storage keys (rename when porting)

| Key | Values |
| --- | --- |
| `embody.theme` | `system` \| `dark` \| `light` |
| `embody.compact` | `1` / `0` |
| `embody.density` | `comfortable` \| `compact` \| `dense` |

Guard all storage I/O with try/catch.

### System theme

- `resolveTheme('system')` → light if `matchMedia('(prefers-color-scheme: light)')`, else dark
- `AppearanceProvider` listens to `change` on that media query while pref is `system`
- Default pref is **`dark`**, not `system`

## Boot / FOUC

1. Import `globals.css` then `appearance.css`
2. Sync `applyAppearance(readStoredAppearance())` before React mount
3. No inline head script in source — light-preferring users may flash dark briefly

CSS must style on **resolved** `data-theme`, never on `system`.

## Consumers

| Surface | Pattern |
| --- | --- |
| DOM / CSS | `html[data-theme='light'|'dark']` + density attrs |
| Chart.js | `useModelChartTheme` → `readModelChartTheme(resolved)` via `getComputedStyle` |
| Three.js | `getThreeSceneTheme` + `watchThreeSceneTheme` (`MutationObserver` on `data-theme`) |
| Settings | `PanelAppearance` in `SettingsModal` |

Chart.js cannot parse `var(...)` — always resolve computed colors after DOM apply.

## Pitfalls

1. FOUC for stored-light users without head inline script
2. Styling on `data-theme-pref` or literal `system` — wrong
3. Compact + dense stacking unexpectedly
4. Imperative 3D mounts need DOM observer, not only React context
5. Hardcoded dark rgba in page CSS forces large light override sheets
6. `--shadow-*` may exist only under light tokens — use fallbacks
7. Disconnect MutationObservers on unmount

## Additional resources

- Attr/API tables and source paths: [reference.md](reference.md)
- Look-and-feel tokens: skill `embody-ui-style`
