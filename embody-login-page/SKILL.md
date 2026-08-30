---
name: embody-login-page
description: >-
  Port Embody Model Eval’s login page UI/UX: centered GitHub-like card,
  teal/amber dark (and light) theme, CSS grid/orb/scan background, locale
  chrome, AuthContext login + RequireAuth `from` redirect. Use when building
  or copying /login for a React+Vite SPA, login.css, LoginPage, auth boot
  screen, or post-login return path — not server cookie/session (see
  cookie-session-auth).
---

# Embody login page

Canonical: `/root/autodl-tmp/embody_model_eval/frontend/src/pages/LoginPage.tsx`,
`styles/login.css` (+ light overrides in `appearance.css`).

**Scope:** public `/login` UI/UX and SPA redirect contract.  
**Not this skill:** cookie/session/PBKDF2 → `cookie-session-auth`.  
**Visual tokens:** prefer `embody-ui-style` / `embody-appearance-theme` / `embody-i18n` as companions.

## Architecture

```text
/login  (public — outside RequireAuth)
  loading → .auth-boot
  !authRequired || authenticated → Navigate(from)
  else → .login-page
           .login-bg (grid / orbs / scan)
           .login-brand (logo + name + lang pill)
           .login-main (.login-card form + .login-aside)
           .login-footer

RequireAuth → Navigate /login state={{ from: path+search+hash }}
```

## Port checklist

```text
- [ ] 1. Public /login route outside the auth gate
- [ ] 2. Gate redirects with from = pathname+search+hash
- [ ] 3. Sanitize from: must start with /, reject // and /login*
- [ ] 4. Boot UI while session probe runs (.auth-boot)
- [ ] 5. If auth off or already signed in → bounce to from
- [ ] 6. Form: username/password, show/hide, busy, role=alert errors
- [ ] 7. credentials: 'same-origin'; map opaque HTTP errors to generic fail copy
- [ ] 8. i18n keys for m.login.* (or single locale)
- [ ] 9. Optional lang pill; theme inherits html[data-theme] (no theme UI required on page)
- [ ] 10. login.css + light overrides; brand asset; prefers-reduced-motion
- [ ] 11. Do not require HomeParticles / PageNav / Settings on login
```

## Page state machine

1. **`loading`** → `.auth-boot` + spinner mark + “checking session” copy  
2. **`!authRequired || authenticated`** → `<Navigate to={from} replace />`  
3. **Form** → submit → `login(user, pass)` → success `navigate(from)` / fail alert

### `from` sanitization (required)

```ts
const raw = state?.from || '/'
if (!raw.startsWith('/') || raw.startsWith('//') || raw.startsWith('/login')) return '/'
return raw
```

## Visual recipe

| Piece | Pattern |
| --- | --- |
| Shell | Full-viewport `.login-page`; centered narrow card (~360px) |
| Atmosphere | `.login-grid` drift, teal/amber `.login-orb-*`, `.login-scan` |
| Brand | Logo + gradient name (text→teal→spark); light theme → solid `--text` |
| Card | Glass `--panel`, top `.login-card-shine`, teal gradient submit |
| Lang | Pill `.login-lang` / `.login-lang-btn.active` |
| Motion | Staggered `login-rise`; kill under `prefers-reduced-motion` |

Reuse Embody tokens (`--bg`, `--accent`, `--spark`, `--panel`). Avoid purple Vite / cream-serif defaults.

## Form / API surface

```ts
login(username, password) → Promise<{ ok: boolean; error?: string }>
// POST /api/auth/login { username, password } credentials: 'same-origin'
```

Error mapping:

- Prefer server `error` string  
- Empty or `/^HTTP \d+$/` → localized `fail`  
- Thrown → `message` or `networkError`

Defaults: seed username to product default (embody uses `'embody'`); empty password; `autoComplete` username / current-password.

## i18n keys (`m.login`)

`loading`, `checkingSession`, `title`, `sub`, `username`, `password`, `show`, `hide`, `submit`, `submitting`, `fail`, `networkError`, `aside`, `asideMuted`, `footerTag`.

Brand product string may stay hardcoded English (“Embody Model Eval”) — generalize per app.

## Class checklist

```text
.login-page .login-bg .login-grid .login-orb .login-orb-a .login-orb-b .login-scan
.login-brand .login-logo .login-brand-name .login-lang .login-lang-btn
.login-main .login-card .login-card-shine .login-sub .login-form
.login-field .login-field-row .login-ghost .login-error .login-submit
.login-aside .login-aside-muted .login-footer .login-footer-dot
.auth-boot .auth-boot-mark   /* shared with RequireAuth */
```

## Pitfalls

1. Open redirect if `from` is not sanitized  
2. Redirect loop if `/login` is accepted as `from`  
3. Auth disabled but page still shown — must Navigate away  
4. Dark-only CSS without light overrides when theme skill is present  
5. Gradient brand text broken in light unless `background-clip` cleared  
6. Confusing login with home (particles / nav / settings)  
7. Global 401 → `/login` can fight React Router — document carefully  
8. Cookie/session details belong in `cookie-session-auth`

## Additional resources

- File map, copy table, CSS notes: [reference.md](reference.md)
- Auth backend: `cookie-session-auth`
- Tokens / theme / locale: `embody-ui-style`, `embody-appearance-theme`, `embody-i18n`
