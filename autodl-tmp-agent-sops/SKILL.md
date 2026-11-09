---
name: autodl-tmp-agent-sops
description: >-
  Agent SOPs to migrate the autodl-tmp / sensors multi-repo workspace from GitHub
  to a new machine, and to copy or recreate fszhangYi GitHub SSH (and gh) auth.
  Use when the user asks 迁移工作区, migrate autodl-tmp, copy SSH key to another PC,
  GitHub 权限复制, sensors-workspace bootstrap on a new host, or SSH over 443.
---

# autodl-tmp agent SOPs

Read the matching markdown end-to-end before acting.

| Doc | Use when |
|-----|----------|
| [agent-sop-migrate-autodl-tmp-workspace.md](agent-sop-migrate-autodl-tmp-workspace.md) | Rebuild the multi-repo workspace on a new computer from GitHub |
| [agent-sop-copy-github-ssh-auth.md](agent-sop-copy-github-ssh-auth.md) | Bring GitHub SSH / `gh` auth to the new computer |

**Order:** auth SOP first (if clone/push needs SSH) → migrate SOP.

**Do not** commit private keys or paste them into chat. Prefer a new key on the destination unless the human explicitly asks to copy the existing `id_ed25519_github`.
