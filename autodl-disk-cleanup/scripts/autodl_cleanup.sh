#!/usr/bin/env bash
# AutoDL disk cleanup: safe tmp/apt purge + migrate large dirs to autodl-tmp.
set -euo pipefail

DATA_ROOT="/root/autodl-tmp"
LOG="${DATA_ROOT}/disk_cleanup.log"
DRY_RUN=0
DO_CHECK=0
DO_APPLY=0
DO_CLEAN_TMP=0
DO_CLEAN_APT=0
DO_CLEAN_PIP=0
DO_MOVE_CONDA=0
MOVE_PATHS=()
KNOWN_VENVS=(GraspVLA_env)

usage() {
  cat <<'EOF'
Usage: autodl_cleanup.sh [options]

  --check          Diagnose only (df + check_disk.py)
  --dry-run        Print actions without changing disk
  --apply          Safe cleanup + move miniconda3 + known venvs

  --clean-tmp      Remove /tmp test artifacts (*.hdf5, convert_*, node tarballs)
  --clean-apt      apt-get clean
  --clean-pip      pip cache purge (if pip available)
  --move-conda     Move /root/miniconda3 to autodl-tmp + symlink
  --move-path P    Move directory P to autodl-tmp + symlink (repeatable)

  -h, --help       Show this help
EOF
}

log() {
  echo "$*" | tee -a "$LOG"
}

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] $*"
  else
    log "[exec] $*"
    eval "$@"
  fi
}

move_to_data_disk() {
  local src="$1"
  local base dest
  [[ -e "$src" ]] || return 0
  if [[ -L "$src" ]]; then
    log "skip (already symlink): $src -> $(readlink "$src")"
    return 0
  fi
  if [[ ! -d "$src" ]]; then
    log "skip (not a directory): $src"
    return 0
  fi
  base="$(basename "$src")"
  dest="${DATA_ROOT}/${base}"
  if [[ -e "$dest" ]]; then
    log "ERROR: destination exists, not overwriting: $dest"
    return 1
  fi
  mkdir -p "$DATA_ROOT"
  run "mv '$src' '$dest'"
  run "ln -s '$dest' '$src'"
  log "migrated: $src -> $dest"
}

clean_tmp() {
  log "cleaning /tmp test artifacts..."
  local patterns=(
    "/tmp/convert_workers_test"
    "/tmp/node-v"*
    "/tmp/node.tar.xz"
    "/tmp/*.hdf5"
    "/tmp/bench_ep"*.hdf5
    "/tmp/test_"*.hdf5
    "/tmp/ep"*_test.json
    "/tmp/quality_report.json"
  )
  for pat in "${patterns[@]}"; do
    for f in $pat; do
      [[ -e "$f" ]] || continue
      run "rm -rf '$f'"
    done
  done
}

clean_apt() {
  log "apt cache clean..."
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] apt-get clean"
    return 0
  fi
  apt-get clean -qq 2>/dev/null || true
  rm -rf /var/cache/apt/archives/*.deb 2>/dev/null || true
}

clean_pip() {
  log "pip cache purge..."
  if command -v pip >/dev/null 2>&1; then
    run "pip cache purge"
  elif [[ -x /root/miniconda3/bin/pip ]]; then
    run "/root/miniconda3/bin/pip cache purge"
  else
    log "pip not found, skip"
  fi
}

verify() {
  log "=== verification ==="
  df -h / "$DATA_ROOT" 2>/dev/null | tee -a "$LOG" || df -h / | tee -a "$LOG"
  if [[ -x /root/miniconda3/bin/python ]]; then
    /root/miniconda3/bin/python -V 2>&1 | tee -a "$LOG"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) DO_CHECK=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --apply)
      DO_APPLY=1
      DO_CLEAN_TMP=1
      DO_CLEAN_APT=1
      DO_MOVE_CONDA=1
      for v in "${KNOWN_VENVS[@]}"; do
        MOVE_PATHS+=("/root/$v")
      done
      ;;
    --clean-tmp) DO_CLEAN_TMP=1 ;;
    --clean-apt) DO_CLEAN_APT=1 ;;
    --clean-pip) DO_CLEAN_PIP=1 ;;
    --move-conda) DO_MOVE_CONDA=1 ;;
    --move-path)
      shift
      [[ $# -gt 0 ]] || { echo "missing path after --move-path"; exit 1; }
      MOVE_PATHS+=("$1")
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1"; usage; exit 1 ;;
  esac
  shift
done

if [[ "$DO_CHECK" -eq 0 && "$DO_APPLY" -eq 0 && "$DO_CLEAN_TMP" -eq 0 && "$DO_CLEAN_APT" -eq 0 \
      && "$DO_CLEAN_PIP" -eq 0 && "$DO_MOVE_CONDA" -eq 0 && ${#MOVE_PATHS[@]} -eq 0 ]]; then
  DO_CHECK=1
fi

mkdir -p "$DATA_ROOT"
echo "" >> "$LOG"
log "=== autodl_cleanup $(date) dry_run=$DRY_RUN ==="
df -h / "$DATA_ROOT" 2>/dev/null | tee -a "$LOG" || true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$DO_CHECK" -eq 1 ]]; then
  python3 "$SCRIPT_DIR/check_disk.py" | tee -a "$LOG" || true
fi

[[ "$DO_CLEAN_TMP" -eq 1 ]] && clean_tmp
[[ "$DO_CLEAN_APT" -eq 1 ]] && clean_apt
[[ "$DO_CLEAN_PIP" -eq 1 ]] && clean_pip
[[ "$DO_MOVE_CONDA" -eq 1 ]] && move_to_data_disk "/root/miniconda3"
for p in "${MOVE_PATHS[@]}"; do
  move_to_data_disk "$p"
done

if [[ "$DO_APPLY" -eq 1 || "$DO_CLEAN_TMP" -eq 1 || "$DO_MOVE_CONDA" -eq 1 || ${#MOVE_PATHS[@]} -gt 0 ]]; then
  verify
fi

log "done. log: $LOG"
