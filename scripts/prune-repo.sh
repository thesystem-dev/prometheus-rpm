#!/usr/bin/env bash
set -euo pipefail

ROOT="runtime/repo"
KEEP=3
DRY_RUN=0
CREATEREPO_BIN=""
MIN_AGE="2h"
MIN_AGE_SECONDS=0
RETAIN_OLD_MD_BY_AGE="2h"
RETENTION_EXPLICIT=false
NO_RETAIN_OLD_MD=false
REPO_MANAGE_DNF=()
REPO_MANAGE_PLAIN=()

usage() {
  cat <<'EOF'
Usage: scripts/prune-repo.sh [--root PATH] [--keep N] [--min-age AGE] [--dry-run]

Prunes old RPM/SRPM files per directory. If a directory already contains
repodata/, refreshes repository metadata after deleting old packages.

Options:
  --root PATH             Repo root (default: runtime/repo)
  --keep N                Keep latest N versions per package (default: 3)
  --min-age AGE           Do not delete packages newer than AGE
                          (default: 2h; examples: 30m, 4h, 1d)
  --no-min-age            Delete old package candidates regardless of age
  --retain-old-md-by-age AGE
                          Retain old createrepo_c metadata after pruning
                          (default: 2h)
  --no-retain-old-md      Do not retain old repository metadata
  --dry-run               Show what would be deleted; do not delete or update metadata
  -h, --help              Show this help
EOF
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

warn() {
  echo "WARNING: $*" >&2
}

require_arg() {
  local option="$1"
  local value="${2:-}"
  [[ -n "$value" && "$value" != --* ]] || die "$option requires an argument"
}

age_to_seconds() {
  local age="$1"
  local value
  local unit

  if [[ "$age" =~ ^([0-9]+)([mhd])$ ]]; then
    value="${BASH_REMATCH[1]}"
    unit="${BASH_REMATCH[2]}"
  else
    die "Invalid age '$age' (use Nm, Nh, or Nd)"
  fi

  case "$unit" in
    m) echo $((value * 60)) ;;
    h) echo $((value * 60 * 60)) ;;
    d) echo $((value * 24 * 60 * 60)) ;;
  esac
}

file_mtime() {
  local path="$1"

  if stat -c %Y "$path" >/dev/null 2>&1; then
    stat -c %Y "$path"
  else
    stat -f %m "$path"
  fi
}

should_keep_for_age() {
  local pkg="$1"

  [[ "$MIN_AGE_SECONDS" -gt 0 ]] || return 1

  local now
  local mtime
  now="$(date +%s)"
  mtime="$(file_mtime "$pkg")"
  (( now - mtime < MIN_AGE_SECONDS ))
}

createrepo_update() {
  local dir="$1"
  local -a args=(--update)

  if [[ "$CREATEREPO_BIN" == "createrepo_c" && "$NO_RETAIN_OLD_MD" != true ]]; then
    args+=(--retain-old-md-by-age "$RETAIN_OLD_MD_BY_AGE")
  fi

  "$CREATEREPO_BIN" "${args[@]}" "$dir" >/dev/null
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      require_arg "$1" "${2:-}"
      ROOT="$2"
      shift 2
      ;;
    --root=*)
      ROOT="${1#*=}"
      [[ -n "$ROOT" ]] || die "--root requires an argument"
      shift
      ;;
    --keep)
      require_arg "$1" "${2:-}"
      KEEP="$2"
      shift 2
      ;;
    --keep=*)
      KEEP="${1#*=}"
      [[ -n "$KEEP" ]] || die "--keep requires an argument"
      shift
      ;;
    --min-age)
      require_arg "$1" "${2:-}"
      MIN_AGE="$2"
      shift 2
      ;;
    --min-age=*)
      MIN_AGE="${1#*=}"
      [[ -n "$MIN_AGE" ]] || die "--min-age requires an argument"
      shift
      ;;
    --no-min-age)
      MIN_AGE=""
      shift
      ;;
    --retain-old-md-by-age)
      require_arg "$1" "${2:-}"
      RETAIN_OLD_MD_BY_AGE="$2"
      RETENTION_EXPLICIT=true
      NO_RETAIN_OLD_MD=false
      shift 2
      ;;
    --retain-old-md-by-age=*)
      RETAIN_OLD_MD_BY_AGE="${1#*=}"
      [[ -n "$RETAIN_OLD_MD_BY_AGE" ]] || die "--retain-old-md-by-age requires an argument"
      RETENTION_EXPLICIT=true
      NO_RETAIN_OLD_MD=false
      shift
      ;;
    --no-retain-old-md)
      NO_RETAIN_OLD_MD=true
      RETENTION_EXPLICIT=true
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! [[ "$KEEP" =~ ^[0-9]+$ ]] || [[ "$KEEP" -lt 1 ]]; then
  die "--keep must be a positive integer"
fi

if [[ -n "$MIN_AGE" ]]; then
  MIN_AGE_SECONDS="$(age_to_seconds "$MIN_AGE")"
fi

if [[ ! -d "$ROOT" ]]; then
  die "Repo root not found: $ROOT"
fi

if dnf repomanage --help >/dev/null 2>&1; then
  REPO_MANAGE_DNF=(dnf repomanage)
fi

if command -v repomanage >/dev/null 2>&1; then
  REPO_MANAGE_PLAIN=(repomanage)
fi

if [[ ${#REPO_MANAGE_DNF[@]} -eq 0 && ${#REPO_MANAGE_PLAIN[@]} -eq 0 ]]; then
  die "repomanage is not available (dnf plugin or standalone command)"
fi

echo "Pruning repo root: $ROOT (keep=$KEEP min_age=${MIN_AGE:-none} dry_run=$DRY_RUN)"

declare -A seen_dirs=()
while IFS= read -r -d '' pkg_file; do
  seen_dirs["$(dirname "$pkg_file")"]=1
done < <(find "$ROOT" -type f \( -name '*.rpm' -o -name '*.src.rpm' \) -print0)
mapfile -t repo_dirs < <(printf '%s\n' "${!seen_dirs[@]}" | sort -u)

if [[ ${#repo_dirs[@]} -eq 0 ]]; then
  echo "No RPM files found under $ROOT"
  exit 0
fi

if [[ "$DRY_RUN" -eq 0 ]]; then
  for dir in "${repo_dirs[@]}"; do
    if [[ -d "$dir/repodata" ]]; then
      if command -v createrepo_c >/dev/null 2>&1; then
        CREATEREPO_BIN="createrepo_c"
      elif command -v createrepo >/dev/null 2>&1; then
        CREATEREPO_BIN="createrepo"
      else
        echo "createrepo_c or createrepo is required to refresh repo metadata under $dir" >&2
        exit 1
      fi
      break
    fi
  done
fi

if [[ -n "$CREATEREPO_BIN" && "$CREATEREPO_BIN" != "createrepo_c" ]]; then
  if [[ "$RETENTION_EXPLICIT" == true && "$NO_RETAIN_OLD_MD" != true ]]; then
    die "--retain-old-md-by-age requires createrepo_c"
  fi
  if [[ "$NO_RETAIN_OLD_MD" != true ]]; then
    warn "createrepo_c not found; old metadata retention is unavailable with $CREATEREPO_BIN"
  fi
fi

for dir in "${repo_dirs[@]}"; do
  repo_manage_cmd=()
  if [[ -d "$dir/repodata" ]]; then
    if [[ ${#REPO_MANAGE_DNF[@]} -gt 0 ]]; then
      repo_manage_cmd=("${REPO_MANAGE_DNF[@]}")
    else
      repo_manage_cmd=("${REPO_MANAGE_PLAIN[@]}")
    fi
  else
    if [[ ${#REPO_MANAGE_PLAIN[@]} -eq 0 ]]; then
      echo "standalone repomanage is required to prune non-repo directories such as $dir" >&2
      exit 1
    fi
    repo_manage_cmd=("${REPO_MANAGE_PLAIN[@]}")
  fi

  mapfile -t old_pkgs < <("${repo_manage_cmd[@]}" --old --keep "$KEEP" "$dir")
  if [[ ${#old_pkgs[@]} -eq 0 ]]; then
    echo "[SKIP] $dir (nothing to prune)"
    continue
  fi

  delete_pkgs=()
  age_skipped=()
  for pkg in "${old_pkgs[@]}"; do
    if should_keep_for_age "$pkg"; then
      age_skipped+=("$pkg")
    else
      delete_pkgs+=("$pkg")
    fi
  done

  if [[ "$DRY_RUN" -eq 1 ]]; then
    for pkg in "${delete_pkgs[@]}"; do
      echo "[DRY] $pkg"
    done
    for pkg in "${age_skipped[@]}"; do
      echo "[KEEP-AGE] $pkg"
    done
    continue
  fi

  if [[ ${#delete_pkgs[@]} -eq 0 ]]; then
    echo "[SKIP] $dir (all ${#age_skipped[@]} prune candidates newer than min-age)"
    continue
  fi

  for pkg in "${delete_pkgs[@]}"; do
    rm -f -- "$pkg"
  done
  echo "[PRUNE] $dir (${#delete_pkgs[@]} files removed, ${#age_skipped[@]} kept by min-age)"

  if [[ -d "$dir/repodata" ]]; then
    createrepo_update "$dir"
    echo "[REPO]  $dir metadata updated"
  fi
done

echo "Done."
