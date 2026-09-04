---
name: embody-settings-modal
description: >-
  Port Embody Model Eval’s homepage Settings gear + modal chrome: overlay
  portal, left-nav tabs, SettingRow / Toggle / Segmented controls, settings.css
  layout, live prefs panels. Use when adding SettingsGear, SettingsDialog,
  preferences modal, settings overlay, or reusing Embody settings layout/style
  in a React+Vite SPA. Defer theme plumbing to embody-appearance-theme, locale
  to embody-i18n, visual tokens to embody-ui-style, sensors embed to
  sensors-view-iframe-embed, auth users to cookie-session-auth.
---

# Embody settings modal

Canonical: `/root/autodl-tmp/embody_model_eval`

| Layer | Path |
| --- | --- |
| UI | `frontend/src/components/SettingsModal.tsx` |
| CSS | `frontend/src/styles/settings.css` |
| Light/density overrides | `frontend/src/styles/appearance.css` (`.settings-*`) |
| Mount | `frontend/src/pages/HomePage.tsx` (header actions only) |
| i18n | `frontend/src/i18n/messages.ts` → `m.settings.*`, `m.common.settings|done|…` |

**Scope:** gear entry, modal shell layout/style, shared row/controls, tab wiring.  
**Not this skill:** appearance prefs API → `embody-appearance-theme`; locale → `embody-i18n`; sensors URL/ping → `sensors-view-iframe-embed`; cookie session / users CRUD → `cookie-session-auth`.  
**Tokens:** `embody-ui-style` (`--accent`, `--panel`, `--chrome`, IBM Plex).

File map & class inventory: [reference.md](reference.md).

## Architecture

```text
HomePage .home-header-actions
  └─ SettingsGear          # local open state
       └─ SettingsDialog   # createPortal → document.body
            overlay (.settings-overlay)
            dialog  (.settings-dialog)
              head  (kicker + title + ×)
              body  grid: nav 200px | panel 1fr
              foot  (esc hint + Done)

Tabs (embody default):
  appearance | language | sensors | auth | users | about
```

**Hard rule:** settings entry lives on the **home overview only**. Other pages use `PageChrome` / `PageNav` without a gear (`PageChrome.tsx` comment).

## Port checklist

```text
- [ ] 1. Copy settings.css; import in SettingsModal (or global CSS entry)
- [ ] 2. Port SettingsGear + SettingsDialog shell (portal, Esc, body scroll lock)
- [ ] 3. Shared primitives: SettingRow, Toggle, Segmented, badge, ghost/primary btn
- [ ] 4. Left-nav tabs from i18n (label + hint); panel switch by SettingsTab
- [ ] 5. Mount gear only on home (or product “hub”) header next to nav
- [ ] 6. Wire live panels you need (appearance / language / …) via companion skills
- [ ] 7. Add m.settings + m.common.* keys (zh/en or single locale)
- [ ] 8. Light theme + density overrides from appearance.css (or restyle with tokens)
- [ ] 9. prefers-reduced-motion: keep fade/rise short; optional kill animations
- [ ] 10. Do not add SettingsGear to every PageChrome unless product asks
```

Minimal viable port = **shell + one tab**. Extra tabs are optional panels, not required chrome.

## Layout recipe (must keep)

| Piece | Pattern |
| --- | --- |
| Entry | Pill `.settings-gear-btn` (icon + label); `aria-haspopup="dialog"` |
| Overlay | `position:fixed; inset:0; z-index:2147483647`; dimmed backdrop; click-outside closes |
| Dialog | `width:min(860px,100%)`; `max-height:min(720px, calc(100vh - 48px))`; column flex; `border-radius:14px` |
| Head | Kicker (uppercase teal) + `h2` + `.settings-close` |
| Body | CSS grid `200px \| 1fr`; left nav scroll; right panel scroll |
| Nav item | Label + muted hint; `.active` teal border/fill |
| Row | Title (+ optional badge) / desc left; control right; `.settings-row-stack` for full-width |
| Foot | Muted Esc hint + `.settings-primary-btn` Done |
| Portal | Always `createPortal(…, document.body)` so z-index clears page chrome |

### Dialog behavior

```ts
// open → body overflow hidden; focus close; Esc → onClose
// overlay click (target === currentTarget) → onClose
// dialog stopPropagation
```

### Shared controls

```ts
SettingRow({ title, desc, badge?, stack?, children })
Toggle({ checked, onChange, label })      // role="switch"
Segmented({ value, options[{id,label}], onChange, ariaLabel })
```

Badges: `m.common.live` (persisted prefs) vs `m.common.placeholder` (non-functional UI).

## CSS contract

Prefix all classes with `settings-`. Copy `settings.css` wholesale when matching Embody; restyle via CSS variables when only layout is reused.

Critical selectors:

| Class | Role |
| --- | --- |
| `.settings-gear-btn` / `-label` | Header pill entry |
| `.settings-overlay` / `-dialog` | Modal shell |
| `.settings-head` / `-kicker` / `-close` | Header |
| `.settings-body` / `-nav` / `-nav-item` / `-panel` | Two-column body |
| `.settings-row*` / `-badge` | Preference rows |
| `.settings-toggle*` / `-seg*` | Controls |
| `.settings-ghost-btn` / `-primary-btn` | Actions |
| `.settings-foot` | Footer |

Light theme: duplicate rules under `html[data-theme='light']` (see `appearance.css`). Density: slightly tighter `.settings-row` padding under compact/dense.

Animations: `@keyframes settings-fade` / `settings-rise` (short; respect reduced-motion if target app already does).

## Tab panels (embody reference)

| Tab | Component | Persistence | Companion |
| --- | --- | --- | --- |
| appearance | `PanelAppearance` | localStorage via `useAppearance` | `embody-appearance-theme` |
| language | `PanelLanguage` | locale/docsLocale | `embody-i18n` |
| sensors | `PanelSensors` | embed URL + ping | `sensors-view-iframe-embed` |
| auth | `PanelAuth` | **none** (placeholder toggles) | — |
| users | `PanelUsers` | `/api/users*` (admin) | `cookie-session-auth` |
| about | `PanelAbout` | static copy | — |

When porting, keep the **shell**; swap or drop panels. Tab id union:

```ts
type SettingsTab = 'appearance' | 'language' | 'sensors' | 'auth' | 'users' | 'about'
// shorten freely — nav is driven by Object.keys(m.settings.tabs)
```

## i18n keys (minimum)

```text
m.common.settings | done | closeSettings | live | placeholder | escHint*
m.settings.title | kicker | navAria
m.settings.tabs.<id>.{label,hint}
m.settings.<panel>.*   # only for panels you ship
```

No settings keys in `pageStrings.ts` — use `messages.ts` tree.

## Pitfalls

1. Mounting gear on every page — breaks embody home-only convention; duplicates prefs entry
2. Rendering dialog in-page without portal — clipped by overflow / loses to nav z-index
3. Forgetting `body.style.overflow` restore on unmount
4. Hardcoding dark dialog gradients without light overrides
5. Putting prefs sync behind `/api/settings` — source app uses localStorage + domain APIs only
6. Copying Users/Sensors panels without their auth/embed backends

## Additional resources

- Class/API tables: [reference.md](reference.md)
- Tokens: skill `embody-ui-style`
- Theme prefs: skill `embody-appearance-theme`
- Locale: skill `embody-i18n`
