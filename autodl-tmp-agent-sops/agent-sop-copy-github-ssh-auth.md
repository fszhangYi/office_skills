# Agent SOP — Copy this machine’s GitHub auth to another computer

**Audience:** Cursor / coding agents helping a human move **GitHub SSH (+ optional `gh` CLI)** from a **source** PC to a **destination** PC.  
**Goal:** Destination can `git clone` / `git push` as user **`fszhangYi`** over SSH without re-inventing keys incorrectly.  
**Companion doc:** [`agent-sop-migrate-autodl-tmp-workspace.md`](agent-sop-migrate-autodl-tmp-workspace.md).

---

## 0. Security rules (non-negotiable)

1. **Never** paste private keys into chat logs, tickets, or commit them into any git repo.  
2. Prefer **encrypted transfer** (1Password, Bitwarden, age/gpg archive, scp over trusted LAN, or OS user profile backup).  
3. Prefer **generating a new key on the destination** and adding the **new public** key on GitHub (cleanest). Copying the private key is allowed only when the human explicitly wants the **same** key identity.  
4. After copying a private key, set filesystem permissions immediately (`chmod 600` on Unix; ACL lockdown on Windows).  
5. Do **not** commit `~/.ssh/id_*`, `config`, or `gh` tokens into `autodl-tmp` or app repos.  
6. If the private key may have been exposed, **rotate**: add new key → verify → revoke old key on GitHub.

---

## 1. What this source machine uses (reference snapshot)

Recorded from the Windows source that runs `autodl-tmp` (update if the human changed names):

| Item | Value |
|------|--------|
| GitHub user | `fszhangYi` |
| Private key file | `~/.ssh/id_ed25519_github` |
| Public key file | `~/.ssh/id_ed25519_github.pub` |
| SSH config host | `github.com` → `ssh.github.com:443` (firewall-friendly) |
| `IdentityFile` | `~/.ssh/id_ed25519_github` |
| `IdentitiesOnly` | `yes` |
| `gh` CLI | Logged in as `fszhangYi`; git protocol **ssh**; token in OS keyring |

Example `~/.ssh/config` fragment to reproduce:

```sshconfig
Host github.com
  HostName ssh.github.com
  Port 443
  User git
  IdentityFile ~/.ssh/id_ed25519_github
  IdentitiesOnly yes
```

Why port **443**: many AutoDL / corporate networks block outbound 22; GitHub accepts SSH over 443 on `ssh.github.com`.

---

## 2. Choose a path

| Path | When to use | Private key moves? |
|------|-------------|--------------------|
| **A. New key on destination (recommended)** | New laptop / shared machine / unsure about key hygiene | No |
| **B. Copy existing key** | Human insists on same deploy identity; offline GitHub UI hard | Yes |
| **C. `gh auth login` only** | HTTPS remotes OK; or SSH via `gh` helper | Optional |

Agents default to **Path A** unless the human says “copy the same key.”

---

## 3. Path A — New Ed25519 key on destination (recommended)

### 3.1 Generate

**Linux / macOS / Git Bash:**

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
ssh-keygen -t ed25519 -C "fszhangYi@$(hostname)-$(date +%Y%m%d)" -f ~/.ssh/id_ed25519_github -N ""
# Prefer nonempty passphrase if human will use ssh-agent daily
chmod 600 ~/.ssh/id_ed25519_github
chmod 644 ~/.ssh/id_ed25519_github.pub
```

**Windows PowerShell:**

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh" | Out-Null
ssh-keygen -t ed25519 -C "fszhangYi@$env:COMPUTERNAME" -f "$env:USERPROFILE\.ssh\id_ed25519_github" -N '""'
```

### 3.2 Write SSH config (§1 fragment)

Ensure `Host github.com` block exists and points at this `IdentityFile`. On Windows the path in `IdentityFile` may be written as `C:/Users/<user>/.ssh/id_ed25519_github` if `~` expansion fails in some clients.

### 3.3 Register public key on GitHub

1. Show pubkey: `Get-Content ~/.ssh/id_ed25519_github.pub` / `cat ~/.ssh/id_ed25519_github.pub`  
2. Human (or agent with `gh`): GitHub → **Settings → SSH and GPG keys → New SSH key**  
   Or: `gh ssh-key add ~/.ssh/id_ed25519_github.pub -t "<machine-name>"`  
3. Title with machine name + date.

### 3.4 Verify

```bash
ssh -T git@github.com
# expect: Hi fszhangYi! You've successfully authenticated...
```

If timeout on port 22, confirm config uses `ssh.github.com` **Port 443**.

```bash
git ls-remote git@github.com:fszhangYi/sensors.git HEAD
```

### 3.5 Optional `gh` CLI

```bash
gh auth login -h github.com -p ssh -w
gh auth status
```

Prefer protocol **ssh** so remotes stay `git@github.com:...`.

---

## 4. Path B — Copy the existing private key from source

Use only with explicit human approval.

### 4.1 On source — inventory (do not print private key material)

```bash
ls -la ~/.ssh/id_ed25519_github ~/.ssh/id_ed25519_github.pub ~/.ssh/config
# Windows: Get-ChildItem $env:USERPROFILE\.ssh
ssh-keygen -lf ~/.ssh/id_ed25519_github.pub   # fingerprint only — OK to show
```

Create an **encrypted** bundle (example with zip + password the human sets, or better `age`):

```bash
# BAD: unencrypted usb copy of private key
# OK-ish: password zip the human controls (still prefer age/1Password)
```

Transfer **only**:

- `id_ed25519_github`  
- `id_ed25519_github.pub`  
- the `Host github.com` block from `config` (not necessarily whole `known_hosts`)

### 4.2 On destination — install files

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
# place key files into ~/.ssh/
chmod 600 ~/.ssh/id_ed25519_github
chmod 644 ~/.ssh/id_ed25519_github.pub
# merge Host github.com block into ~/.ssh/config
chmod 600 ~/.ssh/config
```

**Windows:** keys under `%USERPROFILE%\.ssh\`. Remove inheritance that grants Everyone read if the ACL is too open (Properties → Security). OpenSSH on Windows requires the private key to be readable mainly by the current user.

### 4.3 Verify (same as §3.4)

If auth fails: wrong key file name vs `IdentityFile`, or GitHub no longer has this public key registered.

### 4.4 After successful copy

- Confirm destination fingerprint matches source: `ssh-keygen -lf ...pub`  
- Human may leave the key on both machines; document which hosts share it.  
- Do not leave unencrypted key copies in Downloads / WeChat file drop folders.

---

## 5. Path C — `gh` token / HTTPS (fallback)

If SSH remains blocked:

```bash
gh auth login -h github.com -p https -w
gh auth setup-git
```

Then remotes may be HTTPS. For this workspace, after login still prefer switching remotes to SSH once Path A/B works:

```bash
git remote set-url origin git@github.com:fszhangYi/<repo>.git
```

**Do not** write `gh` tokens into YAML or scripts. Token lives in OS keyring (`gh auth status` shows scopes; source had `repo`, `read:org`, `gist`).

---

## 6. Point all workspace remotes at SSH

After auth works, on every child under the workspace:

```bash
# bash
for d in sensors sensors-view sensors-dcs sensors-arm embody_model_eval \
         office_skills rs-calibration gello gripper_hl; do
  [ -d "$d/.git" ] || continue
  name=$(basename "$d")
  # map folder → repo name (same for this org)
  git -C "$d" remote set-url origin "git@github.com:fszhangYi/${name}.git"
  git -C "$d" remote -v
done
```

Special cases: keep known SSH remotes for `computer-configuration-scan`, `webrtc-preview` if present.

Test push (dry): `git -C sensors push --dry-run` or push a no-op only with human approval.

---

## 7. ssh-agent (optional but recommended)

**Linux:**

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519_github
```

**Windows:** start OpenSSH Authentication Agent service; `ssh-add $env:USERPROFILE\.ssh\id_ed25519_github`.

With passphrase-protected keys, agent avoids repeated prompts for `git fetch` storms across many sub-repos.

---

## 8. Verification checklist

- [ ] `ssh -T git@github.com` greets `fszhangYi`  
- [ ] `~/.ssh/config` uses `ssh.github.com:443` if port 22 is blocked  
- [ ] `IdentityFile` basename matches the key on disk  
- [ ] `IdentitiesOnly yes` (avoids offering wrong default keys)  
- [ ] `git ls-remote git@github.com:fszhangYi/sensors.git` returns refs  
- [ ] (Optional) `gh auth status` → active `fszhangYi`, protocol ssh  
- [ ] No private key path appears in any git `status` / commit  
- [ ] Workspace remotes are `git@github.com:fszhangYi/...`  

---

## 9. Failure modes

| Symptom | Fix |
|---------|-----|
| Timeout / no route port 22 | Use §1 config (`ssh.github.com:443`) |
| `Permission denied (publickey)` | Wrong key, missing GitHub registration, or `IdentitiesOnly` + wrong `IdentityFile` |
| Works in Git Bash but not PowerShell | Different `HOME` / `%USERPROFILE%`; unify config under UserProfile `.ssh` |
| `gh` OK but `git push` fails | Remotes still HTTPS with bad credential helper; set-url to SSH |
| Multiple keys, random failures | Set `IdentitiesOnly yes` and one `IdentityFile` for `Host github.com` |
| Copied key works on A, not B | Line endings / ACL; re-copy raw bytes; `chmod 600` |

---

## 10. What “done” means

Destination authenticates to GitHub as **`fszhangYi` over SSH** (same capability class as the source), can clone and push the sensors stack repos, and has **no** private key material stored inside the workspace git history. Then proceed to the migrate SOP to build `autodl-tmp` / `sensors-workspace`.
