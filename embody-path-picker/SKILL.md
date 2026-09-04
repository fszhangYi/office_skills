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

## Port checklist

```text
- [ ] 1. Backend: fs_browse.py (ROOTS map, list_children, optional browse_roots/stat_path)
- [ ] 2. HTTP: GET /api/fs/children?root=&path=&rootPath= (+ optional /roots, /stat)
- [ ] 3. Types: PathKind, BrowseRoot, StepField.pathKind/browseRoot
- [ ] 4. Client: fetchFsChildren(rootKey, path, rootPath?)
- [ ] 5. PathPickerModal + .path-picker-* CSS (global, not page-prefixed only)
- [ ] 6. FieldInput: path = text + Browse; placeholder by pathKind
- [ ] 7. Page PickerTarget union + single modal instance
- [ ] 8. onConfirm branches: field → setField; root → set root; saveYaml → write API
- [ ] 9. i18n: pathPicker.* (+ page browse labels)
- [ ] 10. credentials: 'same-origin' if cookie auth; gate /api/fs/* like other APIs
```

## Backend recipe

Minimal `list_children`:

1. Resolve `root` from `ROOTS[root_key]` **or** absolute `rootPath` override (must be a dir).
2. Resolve `path` under that root (`Path.resolve` + `relative_to`); else `PermissionError`.
3. List entries; skip `.`* and `__pycache__`; sort dirs first; return:

```json
{
  "ok": true,
  "rootKey": "act|embody|pi05|custom",
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
  value: string                 // seed / current path
  browseRoot: BrowseRoot        // which ROOTS key for API
  roots: Record<BrowseRoot, string>
  pathKind: 'file' | 'dir'
  browseAnchor?: string         // optional listing root override → rootPath
  onClose: () => void
  onConfirm: (path: string) => void
}
```

Effective listing root: `browseAnchor || roots[browseRoot]`.

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
- Change project root → `{ kind: 'root', root }` + `pathKind: 'dir'`, often with `browseAnchor` = parent of current root
- “Save as …” → `{ kind: 'saveYaml' }` + `pathKind: 'file'`

Render **one** `<PathPickerModal>` when `picker != null`; derive `title` / `browseRoot` / `pathKind` / `value` from the union.

### 4. Declarative fields (preferred)

Backend pipeline/spec emits path fields:

```python
{"key": "configPath", "type": "path", "pathKind": "file", "browseRoot": "act"}
{"key": "dataDir", "type": "path", "pathKind": "dir", "browseRoot": "act"}
```

UI loops `fields` and only special-cases `type === 'path'` for the browse button. Do not hardcode every path key in the page.

### 5. Train-YAML side effect (optional)

Selecting `configPath` can `useEffect` → `POST …/load-train-yaml` to merge hyperparams. That is **orthogonal** to the picker; the picker only supplies the path string.

## File vs dir

| | `pathKind: 'dir'` | `pathKind: 'file'` |
| --- | --- | --- |
| Placeholder | directory copy | file copy |
| Listing | files + dirs | files + dirs (no filter) |
| Confirm | draft string | draft string |
| Intent | roots, dataDir, ckptDir | config YAML, scripts, out JSON |

## Do / Don’t

- **Do** keep paths under allowlisted roots (or explicit `rootPath`).
- **Do** allow manual path edit in the modal footer field.
- **Don’t** use browser file inputs for server workspace paths.
- **Don’t** treat `pathKind` as server-side validation unless you add it deliberately.
- **Don’t** put cascade CSS only under a page scope if other pages reuse the modal (embody: global `.path-picker-*`).

## Install

```bash
# from office_skills clone
cp -a embody-path-picker ~/.cursor/skills/embody-path-picker
# or project-level
cp -a embody-path-picker /path/to/workspace/.cursor/skills/embody-path-picker
```
