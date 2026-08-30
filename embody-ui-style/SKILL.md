---
name: embody-ui-style
description: >-
  Port or match Embody Model Eval visual design: teal/spark dark lab-console UI,
  CSS variables, page-prefixed global CSS, glass panels, pill chrome, IBM Plex
  Sans. Use when the user asks for embody UI/style, match embody_model_eval look,
  design tokens, page shells, cards/modals/pills, or CSS architecture without
  Tailwind. Defer deep light/dark toggle plumbing to embody-appearance-theme.
---

# Embody UI style

Canonical reference: `/root/autodl-tmp/embody_model_eval/frontend`
(`src/styles/globals.css`, `appearance.css`, `home.css`, `settings.css`,
`loading.css`, `public/css/ui_motion.css`).

**Stack:** plain global CSS + CSS variables. No Tailwind, CSS Modules, or styled-components.

## When to use

- Match / port the Embody Model Eval look to another React + Vite app
- Add tokens, page shells, cards, modals, pill nav, primary/ghost CTAs
- Keep a dark-first “robotics lab console” identity

## Non-goals

- Auth → `cookie-session-auth`
- Full theme/density prefs plumbing → companion skill `embody-appearance-theme` (Task C)
- i18n → companion skill for LocaleContext (Task D)
- Rewriting to Tailwind unless the user asks

## Visual identity (must keep)

1. **Teal + spark duplex** — primary `#3dd6c6`, warm amber `#f0b429`
2. **Dark navy void** — `--bg: #0b1018` + soft radial `--bg-spot*`
3. **Glass chrome** — translucent `--panel` / `--chrome`, light borders, blur
4. **Pill controls** — `border-radius: 999px` for nav/settings chips
5. **Gradient brand title** — `--brand-title` clipped text
6. **Atmosphere** — grid/orbs/ambience wash + motion tokens (respect reduced-motion)
7. **Dense technical type** — small rem chrome, mono for paths/indices, kickers uppercase

Avoid: purple Vite scaffold, Inter-only stacks, flat single-color backgrounds, Ant Design full theme (icons only OK).

## Architecture

```text
main.tsx → import globals + appearance + loading (+ page CSS per route)
index.html → optional /css/ui_motion.css
html[data-theme] / [data-density] / [data-compact]  ← theme skill owns applyAppearance
:root tokens → .{page}-page → descendant selectors (BEM-ish prefixes)
```

Ignore unused Vite leftovers: `src/index.css`, `src/App.css`.

## Port checklist

```text
- [ ] 1. Copy core CSS: globals.css, appearance.css (or dark tokens only), loading.css, ui_motion.css
- [ ] 2. Import in main.tsx; link ui_motion from index.html (or import)
- [ ] 3. Bundle IBM Plex Sans (@fontsource or Google Fonts) — source app does NOT ship files
- [ ] 4. Set page root class (e.g. .home-page) and use token vars — do not invent a second palette
- [ ] 5. Port chrome: .page-nav-btn, .pill, primary/ghost buttons, panel cards, settings overlay, .emb-load
- [ ] 6. Atmosphere: radial spots + optional ui_motion ambience
- [ ] 7. Charts/Three: read CSS vars / data-theme (see chartTheme.ts, threeTheme.ts)
- [ ] 8. Skip scaffold purple CSS; keep page-prefixed class names
```

Minimal skin: tokens + body font + radial bg + pill button + panel card + teal/spark CTAs.

## Class recipes

| Pattern | Classes / shape |
| --- | --- |
| Page shell | `.{feature}-page` → header / main / optional footer |
| Floating chrome | `.page-nav-floating`, `.page-nav-btn`, portal `.page-nav-menu-portal` |
| Status chip | `.pill` |
| Card | `.card` / `.{page}-card`: `--panel`, 1px border, ~12px radius; hover teal border + slight lift |
| CTA | `.primary` (teal), `.ghost` (border only) |
| Modal | overlay + dialog; head / body / foot; blur scrim |
| Loading | `.emb-load*` — 3-dot teal→spark spinner + shimmer |
| Forms | inputs use `--input-bg`, border, radius ~8px |

State modifiers: space-separated (`active`, `open`, `primary`, `ghost`, `ok`/`warn`/`off`).

## Token cheat sheet (dark)

| Token | Role | Typical |
| --- | --- | --- |
| `--bg` | page void | `#0b1018` |
| `--panel` | glass surface | translucent navy |
| `--text` / `--muted` | copy | `#e7ecf3` / `#8b9bb4` |
| `--accent` / `--accent-dim` | primary teal | `#3dd6c6` |
| `--spark` | second accent | `#f0b429` |
| `--brand-title` | gradient text | text→teal→spark |
| `--surface*` / `--chrome` / `--input-bg` | layered UI | translucent |
| `--bg-spot*` | radial washes | navy/teal |
| `--ui-gap` / `--ui-pad` | density-aware spacing | from `--ui-space` |
| `--motion-ease` / `--motion-fast|med|slow` | motion | in `ui_motion.css` |

Typography: `'IBM Plex Sans', 'Segoe UI', 'PingFang SC', 'Noto Sans SC', sans-serif`; mono for code/paths. Weights often `550–650`. Kickers: uppercase + wide tracking + accent.

Radii: pills `999px`; cards `12px`; modals `14px`; inputs `8px`.

## Pitfalls

1. **No font files in repo** — must load Plex when porting or fallbacks dominate.
2. **Dark hardcodes** — many shadows/borders still raw `rgba`; light overrides live in large `appearance.css`.
3. **Extreme z-index** (~`2147483000`) for nav over 3D/HUD — intentional.
4. **Favicon** may still be Vite purple — replace to match teal/spark.
5. **Density tokens** (`--ui-*`) only cover part of chrome, not every page.
6. Do not treat `index.css` / `App.css` as Embody style.

## Additional resources

- Token tables, file map, density attrs: [reference.md](reference.md)
- Source: `frontend/src/styles/*`, `frontend/public/css/ui_motion.css`, `frontend/src/components/PageNav.tsx`
