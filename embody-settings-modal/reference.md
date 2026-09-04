# Embody settings modal — reference

Derived from `embody_model_eval`. Rename product strings and tab ids when porting.

## Source files

| Path | Role |
| --- | --- |
| `frontend/src/components/SettingsModal.tsx` | `SettingsGear`, `SettingsDialog`, panels, `SettingRow` / `Toggle` / `Segmented` |
| `frontend/src/styles/settings.css` | All `.settings-*` chrome (~788 lines) |
| `frontend/src/styles/appearance.css` | Light + density + EN overrides for `.settings-*` |
| `frontend/src/styles/home.css` | `.home-header-actions` layout next to gear |
| `frontend/src/pages/HomePage.tsx` | Sole mount: `<SettingsGear />` in header |
| `frontend/src/components/PageChrome.tsx` | Documents home-only settings |
| `frontend/src/i18n/messages.ts` | `settings` + `common.settings|done|closeSettings|…` |
| `frontend/src/App.tsx` | Provider stack consumed by panels |
| `frontend/src/prefs/AppearanceContext.tsx` | Appearance tab |
| `frontend/src/i18n/LocaleContext.tsx` | Language tab |
| `frontend/src/prefs/SensorsEmbedContext.tsx` | Sensors tab |
| `frontend/src/auth/usersApi.ts` + `AuthContext.tsx` | Users tab |
| `scripts/agent_server.py` | `/api/sensors-view/ping`, `/api/users*` (not prefs blob) |

## Component map (`SettingsModal.tsx`)

| Name | Lines (approx) | Notes |
| --- | --- | --- |
| `SettingRow` | ~24–49 | Title/desc/badge + control slot |
| `Toggle` | ~51–64 | `role="switch"` |
| `Segmented` | ~66–92 | Pill option group |
| `PanelAppearance` | ~94–131 | Theme / compact / density |
| `PanelLanguage` | ~133–170 | UI + docs locale |
| `PanelSensors` | ~172–247 | URL debounce save + ping |
| `PanelAuth` | ~249–… | Placeholder only |
| `PanelUsers` | ~461–… | Admin CRUD cards |
| `PanelAbout` | ~627–643 | Static list |
| `SettingsDialog` | ~645–750 | Portal shell |
| `SettingsGear` (export) | ~753–773 | Entry + open state |

## DOM structure

```html
<button class="settings-gear-btn">…</button>
<!-- portal -->
<div class="settings-overlay" role="presentation">
  <div class="settings-dialog" role="dialog" aria-modal="true">
    <header class="settings-head">…</header>
    <div class="settings-body">
      <nav class="settings-nav">…</nav>
      <div class="settings-panel" role="tabpanel">…</div>
    </div>
    <footer class="settings-foot">…</footer>
  </div>
</div>
```

## Class inventory (core)

### Shell

- `.settings-gear-btn`, `.settings-gear-label`
- `.settings-overlay`, `.settings-dialog`
- `.settings-head`, `.settings-kicker`, `.settings-close`
- `.settings-body`, `.settings-nav`, `.settings-nav-item`, `.settings-nav-label`, `.settings-nav-hint`
- `.settings-panel`, `.settings-panel-title`
- `.settings-foot`

### Rows / controls

- `.settings-row`, `.settings-row-stack`, `.settings-row-text`, `.settings-row-title`, `.settings-row-desc`, `.settings-row-control`
- `.settings-badge`
- `.settings-toggle`, `.settings-toggle.on`, `.settings-toggle-knob`
- `.settings-seg`, `.settings-seg-btn`, `.settings-seg-btn.active`
- `.settings-ghost-btn`, `.settings-primary-btn`

### Domain panels (optional)

- Users: `.settings-users-*`, `.settings-user-card*`, `.settings-add-user*`
- Sensors: `.settings-sensors-control`, `.settings-sensors-meta`, `.settings-sensors-status-*`, `.settings-sensors-ping`, `.settings-sensors-saved`, `.settings-sensors-hint`
- Tables: `.settings-table*`

### Motion

```css
@keyframes settings-fade { … }
@keyframes settings-rise { … }
```

## Layout numbers (embody defaults)

| Token | Value |
| --- | --- |
| Dialog max width | `min(860px, 100%)` |
| Dialog max height | `min(720px, calc(100vh - 48px))` |
| Nav column | `200px` |
| Overlay z-index | `2147483647` |
| Gear height | `30px`, pill radius `999px` |
| Dialog radius | `14px` |

## Provider stack (when wiring live panels)

```text
LocaleProvider
  AppearanceProvider
    AuthProvider
      SensorsEmbedProvider
        Routes → HomePage → SettingsGear
```

## Persistence (no `/api/settings`)

| Pref | Storage / API |
| --- | --- |
| Theme / compact / density | `embody.theme`, `embody.compact`, `embody.density` |
| Locale / docs locale | `embody.locale`, `embody.docsLocale` |
| Sensors embed URL | `embody.sensorsEmbedUrl` + `GET /api/sensors-view/ping` |
| Users | `GET/POST /api/users`, `PUT/DELETE /api/users/<user>` |

## i18n sketch (`m.settings`)

```ts
settings: {
  title: string
  kicker: string
  navAria: string
  tabs: Record<SettingsTab, { label: string; hint: string }>
  appearance: { theme, themeDesc, themeSystem, themeDark, themeLight, compact, … }
  language: { ui, uiDesc, docs, docsDesc, followUi, applied }
  sensors: { url, urlDesc, urlPlaceholder, ping, pinging, status*, saved, unreachableHint }
  auth: { … }      // placeholder copy
  users: { … }     // CRUD copy
  about: { … }
}
```

Common: `settings`, `done`, `closeSettings`, `live`, `placeholder`, `escHint`, `escHintSaved`, `escHintAppearance`, `escHintSensors`.

## Minimal shell snippet

```tsx
export function SettingsGear() {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button type="button" className="settings-gear-btn" onClick={() => setOpen(true)}>
        {/* icon + label */}
      </button>
      <SettingsDialog open={open} onClose={() => setOpen(false)} />
    </>
  )
}
```

Port panels by composing `SettingRow` + `Toggle`/`Segmented`; keep dialog chrome unchanged.
