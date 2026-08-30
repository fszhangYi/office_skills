# Embody login page — reference

## Source files

| Path | Role |
| --- | --- |
| `frontend/src/pages/LoginPage.tsx` | Page component |
| `frontend/src/styles/login.css` | Login layout + `.auth-boot` |
| `frontend/src/styles/appearance.css` | Light-theme login overrides |
| `frontend/src/App.tsx` | `/login` public; `/login.html` → `/login` |
| `frontend/src/auth/AuthContext.tsx` | `login` / `loading` / `authRequired` |
| `frontend/src/auth/RequireAuth.tsx` | Sets `state.from` |
| `frontend/src/auth/api.ts` | POST `/api/auth/login` |
| `frontend/src/i18n/messages.ts` | `m.login.*` zh/en |
| `frontend/public/favicon.svg` | Brand mark (`/assets/favicon.svg`) |

**Not required:** `HomeParticles`, `PageNav`, `SettingsGear`.

## Component tree

```text
.login-page
  .login-bg [.login-grid, .login-orb-a|b, .login-scan]
  header.login-brand [img.login-logo, .login-brand-name, .login-lang]
  main.login-main
    section.login-card [shine, h1, .login-sub, form.login-form]
    aside.login-aside
  footer.login-footer
```

## Copy (`m.login`)

| Key | zh (approx) | en |
| --- | --- | --- |
| `title` | 登录到 Embody | Sign in to Embody |
| `sub` | 使用本机账号继续 | Use your local account |
| `username` / `password` | 用户名 / 密码 | Username / Password |
| `show` / `hide` | 显示 / 隐藏 | Show / Hide |
| `submit` / `submitting` | 登录 / 登录中… | Sign in / Signing in… |
| `fail` / `networkError` | 登录失败 / 网络错误 | Sign-in failed / Network error |
| `aside` / `asideMuted` | default user + cookie note | same |
| `footerTag` | 本地评测控制台 | Local eval console |
| `loading` / `checkingSession` | 正在加载… / 校验会话… | Loading… / Checking session… |

## Motion inventory (`login.css`)

| Animation | Target |
| --- | --- |
| `login-grid-drift` | `.login-grid` |
| `login-orb-float` | `.login-orb-*` |
| `login-scan` | `.login-scan` |
| `login-shine` | `.login-card-shine` |
| `login-rise` | brand / main / footer entrance |

Disable all under `@media (prefers-reduced-motion: reduce)`.

## Minimal React sketch

```tsx
function sanitizeFrom(raw: string) {
  if (!raw.startsWith('/') || raw.startsWith('//') || raw.startsWith('/login')) return '/'
  return raw
}

// RequireAuth
<Navigate to="/login" replace state={{ from: `${pathname}${search}${hash}` }} />

// LoginPage success
navigate(sanitizeFrom(state?.from || '/'), { replace: true })
```

## Vanilla SPA note

Same DOM/CSS contract works without React: probe `/api/auth/me` → boot or form; on success `location.replace(from)`. Keep open-redirect rules identical.
