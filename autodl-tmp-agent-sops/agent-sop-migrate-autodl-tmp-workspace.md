# Agent SOP — Migrate `autodl-tmp` multi-repo workspace via GitHub

**Audience:** Cursor / coding agents on a **destination** machine.  
**Goal:** Recreate the sensors stack workspace that today lives as `~/Desktop/autodl-tmp` (or equivalent), using **GitHub** as the source of truth — not USB copies of dirty trees.  
**Owner GitHub user:** `fszhangYi`  
**Companion doc:** [`agent-sop-copy-github-ssh-auth.md`](agent-sop-copy-github-ssh-auth.md) (do SSH/`gh` first if pushes or private clones are required).

---

## 0. Critical facts (read before acting)

1. **`autodl-tmp` root is usually NOT a published GitHub repo.**  
   On the source machine it is a **local nest**: `.gitmodules` + per-app git repos. There may be **no** `git remote` on the root.  
   → Migration = **clone each child repo from GitHub** + wire symlinks + venv — **not** `git clone <autodl-tmp>`.

2. **Source of truth for layout and deps** is [`AGENTS.md`](../AGENTS.md) (same content as `sensors/AGENTS.md` after clone). Prefer following that bootstrap; this SOP adds Windows notes, verification, and “what not to copy.”

3. **Do not migrate** by copying: `*.zip` / driver installers, `_dcs_data*`, episode dumps, `_pytest_tmp`, `release/`, `config/users.json`, `.auth.json`, large STL caches outside git, or machine-local `.venv` (recreate venv on the new host).

4. **SSH first** if any repo is private or you must `git push`. Public clones can use HTTPS; this stack standardizes on SSH (`git@github.com:fszhangYi/<repo>.git`).

5. **Default branches differ** — always checkout the table below after clone.

---

## 1. Preconditions (destination machine)

| Check | Pass criteria |
|-------|----------------|
| OS | Linux x86_64 (AutoDL / Ubuntu 20.04+) preferred; Windows 10/11 OK for desktop packs |
| Git | `git --version` ≥ 2.x |
| SSH to GitHub | `ssh -T git@github.com` succeeds (or see companion SOP) |
| Python | ≥ 3.10 (≥ 3.12 recommended if using `embody_model_eval`) |
| Disk | Enough for clones + `.venv` (plan ≥ 5–10 GiB free) |
| Optional | Node 20+ only if rebuilding `embody_model_eval/frontend` |

Agent must **stop and ask the human** if SSH auth fails and private access is required.

---

## 2. Canonical repository table

Clone under one workspace root `WS` (suggested: `$HOME/sensors-workspace` or `C:\Users\<user>\Desktop\autodl-tmp`).

| Local dir | SSH URL | Branch | Required |
|-----------|---------|--------|----------|
| `sensors` | `git@github.com:fszhangYi/sensors.git` | `master` | **Yes** |
| `sensors-view` | `git@github.com:fszhangYi/sensors-view.git` | `master` | **Yes** (UI) |
| `sensors-dcs` | `git@github.com:fszhangYi/sensors-dcs.git` | `master` | If collecting |
| `sensors-arm` | `git@github.com:fszhangYi/sensors-arm.git` | `main` | If arm UI |
| `embody_model_eval` | `git@github.com:fszhangYi/embody_model_eval.git` | **`dev`** | If eval host |
| `office_skills` | `git@github.com:fszhangYi/office_skills.git` | `main` | Recommended for agents |
| `rs-calibration` | `git@github.com:fszhangYi/rs-calibration.git` | **`autodl`** | If calibrating |
| `gello` | `git@github.com:fszhangYi/gello.git` | `main` | Optional probe |
| `gripper_hl` | `git@github.com:fszhangYi/gripper_hl.git` | `main` | Optional |
| `sensors-view` peers | — | — | — |
| Optional extras | `computer-configuration-scan`, `webrtc-preview`, `cad-browser` | see GitHub | No |

**Hard rule:** all hardware drivers / sensor `kind`s live only in **`sensors`**. Apps consume it via symlink; never fork drivers into app trees.

---

## 3. Procedure A — Fresh workspace (recommended)

### 3.1 Create root + clone (bash / Git Bash / WSL)

```bash
set -euo pipefail
WS="${WS:-$HOME/sensors-workspace}"
mkdir -p "$WS"
cd "$WS"

clone() {
  local url="$1" dir="$2" branch="${3:-}"
  if [ -d "$dir/.git" ]; then
    echo "skip clone (exists): $dir"
    git -C "$dir" fetch --all --prune
  else
    git clone "$url" "$dir"
  fi
  if [ -n "$branch" ]; then
    git -C "$dir" checkout "$branch"
    git -C "$dir" pull --ff-only || true
  fi
  git -C "$dir" remote set-url origin "$url" || true
}

clone git@github.com:fszhangYi/sensors.git sensors master
clone git@github.com:fszhangYi/sensors-view.git sensors-view master
clone git@github.com:fszhangYi/sensors-dcs.git sensors-dcs master
clone git@github.com:fszhangYi/sensors-arm.git sensors-arm main
clone git@github.com:fszhangYi/embody_model_eval.git embody_model_eval dev
clone git@github.com:fszhangYi/office_skills.git office_skills main
clone git@github.com:fszhangYi/rs-calibration.git rs-calibration autodl
clone git@github.com:fszhangYi/gello.git gello main
clone git@github.com:fszhangYi/gripper_hl.git gripper_hl main
```

### 3.2 Same on Windows PowerShell (if no bash)

```powershell
$WS = if ($env:WS) { $env:WS } else { "$HOME\sensors-workspace" }
New-Item -ItemType Directory -Force -Path $WS | Out-Null
Set-Location $WS

function Clone-Repo($Url, $Dir, $Branch) {
  if (Test-Path "$Dir\.git") {
    git -C $Dir fetch --all --prune
  } else {
    git clone $Url $Dir
  }
  if ($Branch) {
    git -C $Dir checkout $Branch
    git -C $Dir pull --ff-only
  }
  git -C $Dir remote set-url origin $Url
}

Clone-Repo git@github.com:fszhangYi/sensors.git sensors master
Clone-Repo git@github.com:fszhangYi/sensors-view.git sensors-view master
Clone-Repo git@github.com:fszhangYi/sensors-dcs.git sensors-dcs master
Clone-Repo git@github.com:fszhangYi/sensors-arm.git sensors-arm main
Clone-Repo git@github.com:fszhangYi/embody_model_eval.git embody_model_eval dev
Clone-Repo git@github.com:fszhangYi/office_skills.git office_skills main
Clone-Repo git@github.com:fszhangYi/rs-calibration.git rs-calibration autodl
Clone-Repo git@github.com:fszhangYi/gello.git gello main
Clone-Repo git@github.com:fszhangYi/gripper_hl.git gripper_hl main
```

### 3.3 Symlink `sensors` into apps (required)

**Linux / macOS / Git Bash:**

```bash
cd "$WS"
ln -sfn "$WS/sensors" "$WS/sensors-view/sensors"
ln -sfn "$WS/sensors" "$WS/sensors-dcs/sensors"
ln -sfn "$WS/sensors" "$WS/sensors-arm/sensors"
mkdir -p "$WS/rs-calibration/vendor"
ln -sfn "$WS/sensors/src/sensors" "$WS/rs-calibration/vendor/sensors"
ln -sfn "$WS/sensors/AGENTS.md" "$WS/AGENTS.md" 2>/dev/null || cp -f "$WS/sensors/AGENTS.md" "$WS/AGENTS.md"
```

**Windows (Administrator or Developer Mode for directory junctions):**

```powershell
cd $WS
cmd /c mklink /J sensors-view\sensors sensors
cmd /c mklink /J sensors-dcs\sensors sensors
cmd /c mklink /J sensors-arm\sensors sensors
New-Item -ItemType Directory -Force -Path rs-calibration\vendor | Out-Null
cmd /c mklink /J rs-calibration\vendor\sensors sensors\src\sensors
Copy-Item -Force sensors\AGENTS.md AGENTS.md
```

Do **not** commit the `./sensors` symlink/junction into app repos (already gitignored).

### 3.4 Optional: install Cursor skills from `office_skills`

```bash
mkdir -p "$WS/.cursor/skills"
for s in sensors-view-iframe-embed scheme-a-desktop-compat \
  scheme-a-linux-to-linux-desktop scheme-a-linux-to-windows-desktop \
  cookie-session-auth embody-ui-style; do
  [ -d "$WS/office_skills/$s" ] && cp -a "$WS/office_skills/$s" "$WS/.cursor/skills/$s"
done
```

### 3.5 Python venv + software-only install

```bash
cd "$WS"
python3 -m venv .venv          # Windows: py -3.12 -m venv .venv
source .venv/bin/activate      # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
pip install -e "./sensors[dev]"
pip install -e "./sensors-view"
pip install -e "./sensors-dcs"
pip install -e "./sensors-arm"          # if present
# optional FOV export plots:
pip install -e "./sensors-arm[fov]"     # matplotlib
pip install -r embody_model_eval/requirements.txt
```

Hardware extras only if the station has devices — see `AGENTS.md` / `requirements-hardware.txt`.

On Windows this workspace often uses `scripts/env_python.bat` → activates `WS\.venv` for `sensors-arm\start_run.bat` etc. Recreate that venv; do not copy `.venv` from the old PC.

### 3.6 Smoke test

```bash
source "$WS/.venv/bin/activate"
sensors kinds
sensors list -c sensors/configs/default.yaml
# sensors-view: cwd sensors-view → python -m app.main --host 127.0.0.1 --port 6008
# sensors-arm:  sensors-arm run -c configs/default.yaml --port 6018
# embody:       cd embody_model_eval && ./serve.sh   # :6006
```

| Service | Default port |
|---------|----------------|
| sensors-view | 6008 |
| sensors-arm | 6008 (often override **6018** on multi-app hosts) |
| sensors-dcs viz | 7011 |
| embody_model_eval | 6006 |
| rs-calibration web | 6006 |

---

## 4. Procedure B — Source machine still available (pre-flight)

Before leaving the old PC, agent on **source** should:

1. In each dirty child repo: `git status` → commit (human-approved) → `git push` via SSH.  
2. Confirm remotes are SSH: `git remote get-url origin` → `git@github.com:fszhangYi/<repo>.git`.  
3. Record branch tips: `git -C <repo> rev-parse --short HEAD`.  
4. **Do not** rely on pushing the `autodl-tmp` root unless a remote exists.  
5. Export SSH material per companion SOP (or confirm deploy keys / human will re-auth).

On destination, after Procedure A, optionally pin to recorded SHAs:

```bash
git -C sensors checkout <sha>
# only if human asked for bit-exact tips; otherwise stay on branch tips
```

---

## 5. Procedure C — If a published umbrella repo appears later

If `fszhangYi` publishes a parent repo with `.gitmodules`:

```bash
git clone --recurse-submodules git@github.com:fszhangYi/<umbrella>.git "$WS"
cd "$WS"
git submodule update --init --recursive
# then still run symlink + venv steps (§3.3–3.5)
```

Until that exists, **Procedure A is mandatory**.

---

## 6. Verification checklist (agent must complete)

- [ ] Every required dir has `.git` and `git status -sb` shows tracking `origin/<branch>`  
- [ ] `git -C sensors remote get-url origin` is SSH form  
- [ ] `sensors-view/sensors`, `sensors-dcs/sensors`, `sensors-arm/sensors` resolve to the same `sensors` checkout  
- [ ] `python -c "import sensors; print(sensors.__file__)"` points inside `$WS/sensors`  
- [ ] Smoke: `sensors kinds` OK  
- [ ] No installer zips / `_dcs_data` committed  
- [ ] `AGENTS.md` present at `$WS`  
- [ ] Cursor can open `$WS` as the workspace folder  

---

## 7. Failure modes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `Permission denied (publickey)` | SSH not set up on destination | Companion SOP |
| HTTPS prompts / auth errors | Remote still HTTPS | `git remote set-url origin git@github.com:fszhangYi/<repo>.git` |
| `import sensors` fails in app | Missing symlink | §3.3 |
| Wrong FK / Cell C missing | Wrong branch (e.g. embody on `main` not `dev`) | Checkout table in §2 |
| Port already in use | Another stack on 6008/6006 | Change `--port` / YAML |
| FOV export needs matplotlib | Optional extra not installed | `pip install matplotlib` **into the same venv that runs the app** |
| Windows `mklink` fails | No admin / Developer Mode | Enable Developer Mode or run elevated CMD |

---

## 8. What “done” means

Destination machine has a workspace directory containing the GitHub children on correct branches, `sensors` wired by symlink/junction, a fresh `.venv` with editable installs, and smoke CLI/UI reachable — **without** copying secrets, episode dumps, or the old `.venv` from the source PC.
