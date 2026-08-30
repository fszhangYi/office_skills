# Cookie session auth — reference

Derived from `embody_model_eval`. Rename prefixes when porting.

## Backend files (embody)

| Path | Role |
| --- | --- |
| `scripts/auth.py` | sessions, cookies, `path_requires_auth`, login |
| `scripts/users.py` | `users.json`, PBKDF2, roles, admin CRUD helpers |
| `scripts/agent_server.py` | `_require_auth`, `_require_admin`, route wiring |
| `config/auth.example.json` | committed example |
| `config/users.json` | live users (gitignored) |
| `config/.auth.json` | bootstrap dump (gitignored) |

## Frontend files (embody)

| Path | Role |
| --- | --- |
| `frontend/src/auth/api.ts` | status / me / login / logout |
| `frontend/src/auth/usersApi.ts` | admin user CRUD |
| `frontend/src/auth/AuthContext.tsx` | AuthProvider |
| `frontend/src/auth/RequireAuth.tsx` | route guard |
| `frontend/src/pages/LoginPage.tsx` | login UI |
| `frontend/src/main.tsx` | optional global 401 → `/login` |
| `frontend/src/App.tsx` | `/login` public; app routes under `RequireAuth` |

## API surface

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/api/health` | public | may include `authRequired` |
| GET | `/api/auth/status` | public | `authRequired`, username hint |
| GET | `/api/auth/me` | public | session → user/role or unauthenticated |
| POST | `/api/auth/login` | public | body `{username,password}` → `Set-Cookie` |
| POST | `/api/auth/logout` | public | destroy session → clear cookie |
| * | `/api/users…` | session + **admin** | account CRUD |
| * | other `/api/*` | session if auth on | `_require_auth` |

### Login success cookie

```http
Set-Cookie: embody_session=<token>; HttpOnly; Path=/; SameSite=Lax
```

### Unauthorized body (shape)

```json
{ "ok": false, "authRequired": true, "loginPath": "/login", "error": "unauthorized" }
```

## `path_requires_auth` rules

```python
PUBLIC_API_PATHS = {
    "/api/health",
    "/api/auth/status",
    "/api/auth/login",
    "/api/auth/logout",
    "/api/auth/me",
}
PROTECTED_STATIC_PREFIXES = (
    "/data/",
    "/config/",
    "/agent_skills/",
    "/models/",
)
# /api/* → auth (except PUBLIC_API_PATHS)
# SPA HTML/JS/CSS → NOT server-auth'd
```

## Env vars (embody names)

| Env | Purpose |
| --- | --- |
| `EMBODY_AUTH_DISABLED` | `1`/`true`/`yes`/`on` → auth off |
| `EMBODY_AUTH_USER` | default/bootstrap username (`embody`) |
| `EMBODY_AUTH_PASSWORD` | bootstrap / upsert admin password |

Outbound Chat keys (`CURSOR_API_KEY`, `AGENT_API_KEY`, …) are **not** app login.

## Roles

```python
VALID_ROLES = frozenset({"admin", "eval", "guest"})
```

| Role | Server ACL today |
| --- | --- |
| `admin` | `/api/users*` |
| `eval` | label only |
| `guest` | label only (default) |

## Key signatures

```python
def init_auth() -> dict[str, Any]: ...
def try_login(username: str, password: str) -> dict[str, Any]: ...
def path_requires_auth(path: str) -> bool: ...
def cookie_header_set(token: str) -> str: ...
def is_authenticated(cookie_header: str | None) -> bool: ...
def verify_login(username: str, password: str) -> dict[str, Any] | None: ...
def is_admin(username: str | None) -> bool: ...
```

```ts
export async function login(username: string, password: string): Promise<LoginResponse>
export function RequireAuth({ children }: { children: ReactNode })
export function useAuth(): AuthState
```

## Port naming map

| embody | Port target |
| --- | --- |
| `embody_session` | `<app>_session` |
| `EMBODY_AUTH_*` | `<APP>_AUTH_*` |
| default user `embody` | app-specific default |
| `config/users.json` | keep or rename under app config dir |
