# Embody path picker — reference

Derived from `embody_model_eval`. Rename root keys (`act` / `embody` / `pi05` / `workspace`) when porting.

## Source files

| Path | Role |
| --- | --- |
| `frontend/src/components/PathPickerModal.tsx` | Cascade modal UI + `buildColumns` |
| `frontend/src/features/actPipeline/types.ts` | `PathKind`, `BrowseRoot`, `StepField`, `FsEntry` |
| `frontend/src/features/actPipeline/api.ts` | `fetchFsChildren` |
| `frontend/src/styles/act-pipeline.css` | `.path-picker-*` (~L762–932) |
| `frontend/src/pages/ActPipelinePage.tsx` | `PickerTarget`, `FieldInput`, train YAML save; `rootBrowseAnchor` |
| `frontend/src/pages/Pi05PipelinePage.tsx` | Same pattern; `PI05_BROWSE_SUPERROOT` |
| `scripts/fs_browse.py` | `ROOTS`, `list_children`, `browse_roots`, `stat_path` |
| `scripts/agent_server.py` | `/api/fs/children`, `/roots`, `/stat` |
| `scripts/act_pipeline_runner.py` | Train step field schema (`pathKind` / `browseRoot`) |
| `frontend/src/i18n/pageStrings.ts` | `pathPicker.*`, `act.path*`, `act.btnBrowse` |

Other consumers of the same modal (same abstraction): DatasetConverter, ModelAnalysis, Pi05Setup, Pi05Analysis.

**Known non-React port:** `sensors-dcs` (`src/sensors_dcs/fs_browse.py`, path-picker block in `viz.py` PREVIEW_HTML) — Settings → 配置文件.

## Types (copy shape)

```ts
export type PathKind = 'file' | 'dir'
export type BrowseRoot = 'act' | 'embody' | 'pi05'  // extend per app (e.g. 'workspace')

export interface StepField {
  key: string
  label: string
  type: 'path' | 'text' | 'number' | 'select' | 'checkbox'
  pathKind?: PathKind
  browseRoot?: BrowseRoot
  hint?: string
  // ...
}

export interface FsEntry {
  name: string
  path: string
  isDir: boolean
}
```

## Client API

```ts
export function fetchFsChildren(rootKey: string, path = '', rootPath?: string) {
  const qs = new URLSearchParams({ root: rootKey })
  if (path) qs.set('path', path)
  if (rootPath) qs.set('rootPath', rootPath)
  return api<FsListResponse>(`/api/fs/children?${qs}`)
}
```

| Endpoint | Purpose |
| --- | --- |
| `GET /api/fs/children?root=&path=&rootPath=` | Cascade listing |
| `GET /api/fs/roots` | Default root map |
| `GET /api/fs/stat?path=&expect=` | Health probe (setup), not cascade |

### Children response

```json
{
  "ok": true,
  "rootKey": "act",
  "root": "/abs/root",
  "path": "/abs/cwd",
  "entries": [
    { "name": "configs", "path": "/abs/root/configs", "isDir": true },
    { "name": "train.yaml", "path": "/abs/root/train.yaml", "isDir": false }
  ]
}
```

### `fs_browse` security

- Default roots from module constants (`ACT_ROBOT_ROOT`, `EMBODY_ROOT`, `PI05_ROOT`) or app helpers (`project_root().parent` as `workspace`).
- `rootPath` → custom root (`rootKey` becomes `"custom"`); still must be a directory.
- Target must be under root via `Path.resolve` + `relative_to`.
- Hidden names (`.`*) and `__pycache__` skipped.

## Sandbox vs seed (API mapping)

```text
Modal props                API query
─────────────────────      ────────────────────────────
browseAnchor
  || roots[browseRoot]  →  rootPath  (and listing root)
value / draft seed      →  path walk via relParts only
```

`buildColumns(browseRoot, rootPath, seed)` calls:

```ts
fetchFsChildren(rootKey, rootPath, rootPath)           // first column = sandbox listing
fetchFsChildren(rootKey, hit.path, rootPath)           // deeper columns; rootPath unchanged
```

Wrong (common port bug):

```ts
// seed = "/repo/configs/app.yaml"
browseAnchor = dirname(seed)   // → chroot becomes …/configs — cannot see siblings
```

Right for field browse:

```ts
browseRoot = 'workspace'       // ROOTS.workspace = project_root().parent
browseAnchor = undefined
value = seed                   // expand columns toward current file
```

Right for “change project root” (embody Act):

```ts
browseAnchor = parent(currentRoot) || '/root/autodl-tmp'  // widen chroot one level
pathKind = 'dir'
```

## Page confirm branches (ACT)

```ts
const onPickerConfirm = (path: string) => {
  if (!picker) return
  if (picker.kind === 'root') {
    // applyEmbodyRoot / applyActRoot
  } else if (picker.kind === 'saveYaml') {
    void doSaveTrainYaml(path)
  } else if (linkReady) {
    setField(picker.field.key, path)
  }
  setPicker(null)
}
```

Modal prop derivation:

| `picker.kind` | `browseRoot` | `pathKind` | `browseAnchor` |
| --- | --- | --- | --- |
| `field` | `field.browseRoot \|\| 'act'` | `field.pathKind \|\| 'dir'` | — (keep sandbox = `roots[browseRoot]`) |
| `root` | `picker.root` | `'dir'` | parent-of-current / superroot |
| `saveYaml` | `'act'` (or app default) | `'file'` | — |

## CSS classes

Keep selectors **global** (`.path-picker-*`), not only under `.act-pipeline-page`:

| Class | Role |
| --- | --- |
| `.path-picker-overlay` | Full-screen scrim, z-index high |
| `.path-picker-dialog` | Modal shell |
| `.path-picker-head` / `-close` | Title + dismiss |
| `.path-picker-root` | Shows effective root |
| `.path-picker-err` | List/fetch errors |
| `.path-picker-cascade` | Horizontal column scroller |
| `.path-picker-col` | One directory column (`ul`) |
| `.path-picker-item` `.dir` / `.file` | Entry buttons |
| `.path-picker-edit` | Editable absolute path |
| `.path-picker-foot` / `-btn` | Cancel / Confirm |

Tokens used: `--overlay-scrim`, `--text`, `--muted`, `--accent`, `--accent-dim`.

Field chrome (page-local): `.act-path-field`, `.act-path-browse`.

## i18n keys (minimal set)

```text
pathPicker.cancel
pathPicker.cascade
pathPicker.closeAria
pathPicker.confirm
pathPicker.dirPlaceholder
pathPicker.filePlaceholder
pathPicker.loading
pathPicker.pathEdit
pathPicker.root
act.btnBrowse
act.pathDirPlaceholder
act.pathFilePlaceholder
act.pathBrowseTitle   # "Browse {root}"
```

Hardcode strings if the target app has no i18n; keep keys stable if porting with `embody-i18n`.

## Train hyperparam example fields

From `act_pipeline_runner.py` train step:

| key | pathKind | Notes |
| --- | --- | --- |
| `configPath` | file | Select → load-train-yaml fills HPs |
| `dataDir` | dir | HDF5 input |
| `ckptDir` | dir | Checkpoint output |
| `resumeFrom` | file | Optional resume checkpoint |

Save-as-YAML uses the same modal (`kind: 'saveYaml'`), independent of Run.

## Porting tips

1. Start with `fs_browse.py` + one root key; prefer `project_root().parent` as the primary sandbox unless the product is intentionally locked to one subtree.
2. Copy `PathPickerModal.tsx` almost verbatim; swap `t()` for literals or your i18n. For FastAPI HTML monoliths, port the same cascade JS/CSS without React.
3. Extract CSS block into `path-picker.css` if the host has no `act-pipeline.css`.
4. Prefer schema-driven `StepField` over ad-hoc browse buttons when the page already has a field schema.
5. If auth exists (`cookie-session-auth`), protect `/api/fs/*` like other `/api` routes.
6. Keep picker Confirm = “fill path”; put validate / persist / restart on a separate button when those are destructive.
7. Embedded JS in Python triple-quoted HTML: write path-split regexes as `[/\\\\]`, not `\/`, to avoid `SyntaxWarning: invalid escape sequence`.
