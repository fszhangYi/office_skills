# Embody appearance theme — reference

## Source files

| Path | Role |
| --- | --- |
| `frontend/src/prefs/appearance.ts` | Types, storage, resolve, apply |
| `frontend/src/prefs/AppearanceContext.tsx` | Provider + system listener |
| `frontend/src/main.tsx` | Pre-React `applyAppearance` |
| `frontend/src/App.tsx` | Provider wrap |
| `frontend/src/components/SettingsModal.tsx` | `PanelAppearance` |
| `frontend/src/styles/globals.css` | Dark tokens on `:root` / `html[data-theme='dark']` |
| `frontend/src/styles/appearance.css` | Light tokens + overrides + density |
| `frontend/src/features/modelAnalysis/chartTheme.ts` | Chart color bridge |
| `frontend/src/features/modelAnalysis/useModelChartTheme.ts` | Hook |
| `frontend/src/lib/threeTheme.ts` | Three scene theme + watcher |
| `frontend/src/i18n/messages.ts` | `settings.appearance.*` |

## DOM contract

| Attribute / style | Set by | Consumed by |
| --- | --- | --- |
| `data-theme` | `applyAppearance` (resolved) | CSS, Three, charts |
| `data-theme-pref` | `applyAppearance` (raw) | diagnostics / future UI |
| `data-density` | prefs | `--ui-space` / `--ui-font-scale` |
| `data-compact` | prefs | `--ui-header-pad-y` shrink |
| `style.colorScheme` | prefs | native controls |

## CSS layering

```css
:root,
html[data-theme='dark'] { /* dark tokens */ }

html[data-theme='light'] {
  /* same var names, light values */
  color-scheme: light;
}

html[data-density='compact'] { /* --ui-space ≈ 0.9 */ }
html[data-density='dense'] { /* --ui-space ≈ 0.82 */ }
html[data-compact='1'] { /* tighter header pad */ }
```

Light polish may also target `html[data-theme='light'] .page…` for hardcoded dark leftovers.

## Minimal copy-paste shape (`appearance.ts`)

```ts
export type ThemePref = 'system' | 'dark' | 'light'
export type DensityPref = 'comfortable' | 'compact' | 'dense'
export type AppearancePrefs = {
  theme: ThemePref
  compact: boolean
  density: DensityPref
}

export function resolveTheme(pref: ThemePref): 'dark' | 'light' {
  if (pref === 'light' || pref === 'dark') return pref
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

export function applyAppearance(prefs: AppearancePrefs): 'dark' | 'light' {
  const resolved = resolveTheme(prefs.theme)
  const root = document.documentElement
  root.dataset.theme = resolved
  root.dataset.themePref = prefs.theme
  root.dataset.compact = prefs.compact ? '1' : '0'
  root.dataset.density = prefs.density
  root.style.colorScheme = resolved
  return resolved
}
```

Rename `embody.*` storage keys when porting.
