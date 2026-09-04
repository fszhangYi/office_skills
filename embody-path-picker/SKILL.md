---
name: embody-path-picker
description: >-
  Port Embody Model Eval’s server-scoped cascade PathPickerModal: text+Browse
  path fields, PickerTarget (field|root|saveYaml), GET /api/fs/children via
  fs_browse.py, file vs dir pathKind. Use when adding path browse dialogs,
  folder/file pickers, PathPickerModal, browseRoot, pathKind, or replacing
  native OS file inputs for lab SPAs that browse server disks.
---

# Embody path picker (server cascade)

Canonical: `/root/autodl-tmp/embody_model_eval`

| Layer | Path |
| --- | --- |
| Modal | `frontend/src/components/PathPickerModal.tsx` |
| Types | `frontend/src/features/actPipeline/types.ts` (`PathKind`, `BrowseRoot`, `StepField`) |
| Client API | `frontend/src/features/actPipeline/api.ts` → `fetchFsChildren` |
| CSS | `frontend/src/styles/act-pipeline.css` (`.path-picker-*`, ~762+) |
| Backend | `scripts/fs_browse.py` |
| Routes | `scripts/agent_server.py` → `/api/fs/children`, `/api/fs/roots`, `/api/fs/stat` |
| Wiring | `ActPipelinePage.tsx` / `Pi05PipelinePage.tsx` (`PickerTarget`) |

**Not this skill:** native `<input type="file">`, OS file dialogs, or client-only File System Access API.  
**Companions:** `embody-ui-style` (tokens), `embody-i18n` (`pathPicker.*` keys).

File map & contracts: [reference.md](reference.md).

## Architecture

```text
StepField { type:'path', pathKind:'file'|'dir', browseRoot }
  → FieldInput: <input text> + Browse button
  → setPicker({ kind:'field'|'root'|'saveYaml', ... })
  → PathPickerModal
       open → buildColumns(seed) via GET /api/fs/children
       click dir → next cascade column
       click file / edit draft → draft path
       Confirm → onConfirm(draft.trim())
  → page applies: setField | setRoot | saveYaml API

fs_browse.list_children(root_key, path, root_path?)
  paths must stay under ROOTS[root] or custom rootPath
```

**Hard rule:** browsing is **server-side and sandbox-scoped**. Never expose arbitrary `/` listing without a root allowlist.

## Critical: sandbox root vs seed path

Two different strings — do not conflate them:

| Concept | Role | Typical value |
| --- | --- | --- |
| **Sandbox root** | Chroot for every `/api/fs/children` call (`roots[browseRoot]` or `browseAnchor` → `rootPath`) | Parent of project / lab superroot |
| **Seed / value** | Current field path; only drives cascade column focus via `relParts` | e.g. `…/myapp/configs/foo.yaml` |

`PathPickerModal` sets `rootPath = browseAnchor || roots[browseRoot]` and passes that same string as `rootPath` on **every** fetch. So:

- **Do** keep sandbox fixed for a given picker open (usually a stable ROOTS entry).
- **Do** pass the current file/dir path only as `value` / draft seed so columns expand to it.
- **Don’t** set `browseAnchor` (or inline `rootPath`) to the seed file’s parent — that shrinks the chroot to one folder and users cannot walk up to siblings.
- **Do** use `browseAnchor` only when intentionally changing the chroot (embody `kind: 'root'`: parent of current project root / `PI05_BROWSE_SUPERROOT`).

### Choosing default ROOTS

For “pick a config anywhere near this repo” UIs (Settings → 配置文件, etc.):

```python
# Preferred primary key for lab tools on AutoDL / shared disks
"workspace": project_root().resolve().parent   # NOT project_root(), NOT …/configs
```

Embody π0.5 hardcodes the same idea (`PI05_BROWSE_SUPERROOT = '/root/autodl-tmp'`). Narrow roots (`…/configs`, user-data only) are optional shortcuts — not the default sandbox for a general file picker.

## Port checklist

```text
- [ ] 1. Backend: fs_browse.py (ROOTS map, list_children, optional browse_roots/stat_path)
- [ ] 2. Decide primary ROOT: usually project_root().parent (document key name)
- [ ] 3. HTTP: GET /api/fs/children?root=&path=&rootPath= (+ optional /roots, /stat)
- [ ] 4. Types: PathKind, BrowseRoot, StepField.pathKind/browseRoot (or page-local equivalents)
- [ ] 5. Client: fetchFsChildren(rootKey, path, rootPath?) — sandbox ≠ seed
- [ ] 6. PathPickerModal + .path-picker-* CSS (global, not page-prefixed only)
- [ ] 7. FieldInput: path = text + Browse; placeholder by pathKind
- [ ] 8. Page PickerTarget union + single modal instance (or one overlay in HTML apps)
- [ ] 9. onConfirm → fill field only; apply/save/restart is a separate control if needed
- [ ] 10. i18n: pathPicker.* (+ page browse labels)
- [ ] 11. credentials: 'same-origin' if cookie auth; gate /api/fs/* like other APIs
```

## Backend recipe

Minimal `list_children`:

1. Resolve `root` from `ROOTS[root_key]` **or** absolute `rootPath` override (must be a dir).
2. Resolve `path` under that root (`Path.resolve` + `relative_to`); else `PermissionError`.
3. List entries; skip `.`* and `__pycache__`; sort dirs first; return:

```json
{
  "ok": true,
  "rootKey": "act|embody|pi05|workspace|custom",
  "root": "/abs/root",
  "path": "/abs/cwd",
  "entries": [{ "name": "...", "path": "/abs/...", "isDir": true }]
}
```

Wire in the HTTP handler (embody `agent_server.py` pattern): catch `ValueError|PermissionError|NotADirectoryError` → 400 JSON `{ok:false, error}`.

Optional:

- `GET /api/fs/roots` → default root map for UI
- `GET /api/fs/stat?path=&expect=dir|file|…` → setup health rows (not the cascade)

## Frontend recipe

### 1. Modal props

```ts
interface PathPickerModalProps {
  open: boolean
  title: string
  value: string                 // seed / current path (cascade focus only)
  browseRoot: BrowseRoot        // which ROOTS key for API
  roots: Record<BrowseRoot, string>
  pathKind: 'file' | 'dir'
  browseAnchor?: string         // optional chroot override → rootPath (not seed’s parent!)
  onClose: () => void
  onConfirm: (path: string) => void
}
```

Effective **sandbox**: `browseAnchor || roots[browseRoot]`.  
Effective **seed**: `value` (fallback to sandbox when empty).

### 2. Cascade behavior

- `buildColumns`: walk `relParts(root, seed)`, fetching children per directory.
- Dir click: append column; update `draft`.
- File click: set `draft`; if `pathKind === 'file'`, trim columns after current depth.
- Confirm: **no hard file/dir validation** — return `draft.trim()` (user may type any abs path).

### 3. Page wiring (`PickerTarget`)

```ts
type PickerTarget =
  | { kind: 'field'; field: StepField }
  | { kind: 'root'; root: BrowseRoot }
  | { kind: 'saveYaml' }   // optional; omit if unused
```

- Browse on path field → `{ kind: 'field', field }`
- Change project root → `{ kind: 'root', root }` + `pathKind: 'dir'`, often with `browseAnchor` = **parent of current root** (widen chroot)
- “Save as …” → `{ kind: 'saveYaml' }` + `pathKind: 'file'`

Render **one** `<PathPickerModal>` when `picker != null`; derive `title` / `browseRoot` / `pathKind` / `value` from the union.

### 4. Declarative fields (preferred)

Backend pipeline/spec emits path fields:

```python
{"key": "configPath", "type": "path", "pathKind": "file", "browseRoot": "act"}
{"key": "dataDir", "type": "path", "pathKind": "dir", "browseRoot": "act"}
```

UI loops `fields` and only special-cases `type === 'path'` for the browse button. Do not hardcode every path key in the page.

### 5. Side effects after path (orthogonal)

The picker **only** returns a path string. Loading YAML, writing `active_config`, restarting the process, etc. belong on a separate Confirm/Apply control (or `useEffect` on the field) — same pattern as embody train `load-train-yaml`.

### 6. Non-React / monolith HTML hosts

Same contracts work inside a FastAPI-served HTML string (e.g. sensors-dcs `viz.py`):

- Copy `.path-picker-*` CSS + overlay markup once.
- One JS state object + `fetchFsChildren` / `buildPickerColumns` / `openPathPicker`.
- Open: `rootPath = roots.workspace` (fixed); `draft = currentConfigPath` (seed).
- If JS lives inside a Python `"""…"""` string, avoid regex literals with `\/` (Python `SyntaxWarning`); prefer character classes like `[/\\\\]`.

## File vs dir

| | `pathKind: 'dir'` | `pathKind: 'file'` |
| --- | --- | --- |
| Placeholder | directory copy | file copy |
| Listing | files + dirs | files + dirs (no filter) |
| Confirm | draft string | draft string |
| Intent | roots, dataDir, ckptDir | config YAML, scripts, out JSON |

## Do / Don’t

- **Do** keep paths under allowlisted roots (or explicit `rootPath`).
- **Do** default sandbox to parent-of-project when users need sibling trees.
- **Do** allow manual path edit in the modal footer field.
- **Don’t** use browser file inputs for server workspace paths.
- **Don’t** treat `pathKind` as server-side validation unless you add it deliberately.
- **Don’t** put cascade CSS only under a page scope if other pages reuse the modal (embody: global `.path-picker-*`).
- **Don’t** reuse the seed file’s parent as `browseAnchor` / `rootPath`.

## Install

```bash
# from office_skills clone
cp -a embody-path-picker ~/.cursor/skills/embody-path-picker
# or project-level
cp -a embody-path-picker /path/to/workspace/.cursor/skills/embody-path-picker
```
