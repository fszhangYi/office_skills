---
name: cookie-session-auth
description: >-
  Port or implement Cookie + server-side opaque session auth for local Python
  HTTP tools with a React SPA (embody_model_eval pattern): HttpOnly cookie,
  PBKDF2 users store, public /api/auth/*, blanket /api gate, RequireAuth, and
  admin-only user CRUD. Use when adding login/logout, session cookies,
  EMBODY_AUTH_*, users.json, RequireAuth, authRequired, or protecting /api and
  sensitive static paths without JWT/OAuth.
---

# Cookie session auth (embody_model_eval pattern)

Canonical reference: `/root/autodl-tmp/embody_model_eval` (`scripts/auth.py`,
`scripts/users.py`, `scripts/agent_server.py`, `frontend/src/auth/*`).

Stack: **stdlib `http.server`** (or any plain HTTP handler) + **React Router**.
Do **not** invent JWT/OAuth unless the user explicitly asks.

## When to use

- Add login to a local lab UI (AutoDL / same-origin Vite proxy)
- Protect `/api/*` and sensitive static trees (`/data`, `/config`, `/models`, …)
- Multi-user accounts with hashed passwords + optional admin CRUD
- Kill-switch env to disable auth for debugging

## Architecture (must keep)

```text
SPA AuthProvider → GET /api/auth/me
RequireAuth → /login if authRequired && !authenticated
login → POST /api/auth/login → Set-Cookie: <app>_session=… (HttpOnly; SameSite=Lax)
fetch(*, credentials: 'same-origin')
Server: path_requires_auth → cookie → in-memory session TTL
Admin-only: is_admin for /api/users*
```

Defense in depth:

| Layer | Protects | Does not protect |
| --- | --- | --- |
| SPA `RequireAuth` | UX / route shells | HTML/JS assets (still public) |
| Server `_require_auth` | `/api/*` + sensitive static | Public auth endpoints + SPA assets |

## Port checklist

Copy this and tick as you go:

```text
- [ ] 1. Credential store (users.json + PBKDF2; gitignore; *.example.json)
- [ ] 2. Session module (opaque token, cookie parse/set, TTL, compare_digest)
- [ ] 3. Public endpoints: status / me / login / logout (+ health)
- [ ] 4. Gate non-public /api/* when auth enabled
- [ ] 5. Gate sensitive static prefixes; leave SPA assets public
- [ ] 6. SPA: AuthProvider + RequireAuth + LoginPage + credentials: 'same-origin'
- [ ] 7. Admin: _require_admin only on account mutation APIs
- [ ] 8. Ops: AUTH_DISABLED / AUTH_USER / AUTH_PASSWORD + one-time bootstrap print
- [ ] 9. 401 JSON shape + frontend redirect (allowlist auth endpoints)
- [ ] 10. Never commit secrets; never log passwords after bootstrap
```

## Backend recipe

### 1. Modules

Prefer two modules (as in embody):

- `auth.py` — sessions, cookies, `path_requires_auth`, `try_login`, `init_auth`
- `users.py` — `users.json` CRUD, PBKDF2 verify, roles, `is_admin`

Hash format: `pbkdf2_sha256$iters$salt_hex$digest_hex` (~120k iters). Verify with
`secrets.compare_digest`.

### 2. Cookie

- Name: `<app>_session` (embody uses `embody_session`)
- Flags: `HttpOnly; Path=/; SameSite=Lax` (omit `Secure` only when serving plain HTTP, e.g. AutoDL)
- Store: process-memory dict `{token → {username, role, expires}}` with sliding TTL (embody: 7d)
- Restart clears sessions (document this)

### 3. Public vs protected

Public API (no cookie):

- `/api/health`, `/api/auth/status`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`

Protected:

- All other `/api/*`
- Sensitive static prefixes (embody: `/data/`, `/config/`, `/agent_skills/`, `/models/`)

SPA shells (`/`, `/index.html`, `/assets/*`, Vite `dist`) stay **public**; secrets must not live only behind client routes.

### 4. Handler wiring

On every mutating/sensitive request, before business logic:

```python
def _require_auth(self, path: str) -> bool:
    if not path_requires_auth(path):
        return True
    if is_authenticated(self.headers.get("Cookie")):
        return True
    self._unauthorized()  # 401 JSON: authRequired, loginPath
    return False
```

Admin-only user CRUD:

```python
def _require_admin(self) -> dict | None:
    # session user + users.is_admin → else 403
```

Call `init_auth()` once at process start.

### 5. Env / files (names only)

| Name | Role |
| --- | --- |
| `<APP>_AUTH_DISABLED` | truthy → auth off |
| `<APP>_AUTH_USER` | bootstrap / primary username |
| `<APP>_AUTH_PASSWORD` | bootstrap / upsert admin password |
| `config/users.json` | multi-user store (gitignore) |
| `config/.auth.json` | legacy/bootstrap dump (gitignore) |
| `config/auth.example.json` | committed example |

When auth disabled: `/api/auth/me` reports `authRequired: false`, treat as authenticated; gates no-op.

## Frontend recipe

Directory: `frontend/src/auth/` (`api.ts`, `AuthContext.tsx`, `RequireAuth.tsx`, optional `usersApi.ts`).

1. **AuthProvider** — boot with `GET /api/auth/me`; expose `login` / `logout` / `refresh`.
2. **RequireAuth** — while loading show boot UI; if `authRequired && !authenticated` → `<Navigate to="/login" state={{ from }} />`.
3. **LoginPage** — POST login; on success navigate to `from` or home.
4. **All authenticated fetches** — `credentials: 'same-origin'`.
5. **Global 401** (optional) — wrap `fetch`; redirect to `/login` except auth/chat endpoints that handle 401 in-page.
6. **Admin UI** — gate on `user.role === 'admin'`; still enforce on server.

Vite: proxy `/api` (and protected static) to the Python port so cookies stay same-origin in dev.

## Roles

embody defines `admin | eval | guest`, but **only admin is ACL-enforced** (user management). Do not assume `eval`/`guest` block feature APIs unless you add path ACLs.

## Pitfalls

1. SPA guards ≠ security — always gate `/api` and sensitive static on the server.
2. Missing `credentials: 'same-origin'` → forever logged out.
3. In-memory sessions die on restart / multi-process workers.
4. Cookie without `Secure` is wrong for HTTPS-only production.
5. Confusing Chat/LLM `Authorization: Bearer` with app login cookies.
6. CORS `*` + credentialed cross-origin — do not design for that; keep same-origin.
7. 401 redirect loops if login endpoints are not allowlisted.
8. Committing `users.json` / `.auth.json` / plaintext passwords.

## Additional resources

- Endpoint / env / path tables: [reference.md](reference.md)
- Source of truth in embody_model_eval: `scripts/auth.py`, `scripts/users.py`, `frontend/src/auth/`
