#!/usr/bin/env bash
set -euo pipefail

ROOT="runtime/repo"
KEEP=3
DRY_RUN=0
CREATEREPO_BIN=""
REPO_MANAGE_DNF=()
REPO_MANAGE_PLAIN=()

usage() {
  cat <<'EOF'
Usage: scripts/prune-repo.sh [--root PATH] [--keep N] [--dry-run]

Prunes old RPM/SRPM files per directory. If a directory already contains
repodata/, refreshes repository metadata after deleting old packages.

Options:
  --root PATH   Repo root (default: runtime/repo)
  --keep N      Keep latest N versions per package (default: 3)
  --dry-run     Show what would be deleted; do not delete or update metadata
  -h, --help    Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      ROOT="$2"
      shift 2
      ;;
    --keep)
      KEEP="$2"
      shift 2
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
  echo "--keep must be a positive integer" >&2
  exit 1
fi

if [[ ! -d "$ROOT" ]]; then
  echo "Repo root not found: $ROOT" >&2
  exit 1
fi

if dnf repomanage --help >/dev/null 2>&1; then
  REPO_MANAGE_DNF=(dnf repomanage)
fi

if command -v repomanage >/dev/null 2>&1; then
  REPO_MANAGE_PLAIN=(repomanage)
fi

if [[ ${#REPO_MANAGE_DNF[@]} -eq 0 && ${#REPO_MANAGE_PLAIN[@]} -eq 0 ]]; then
  echo "repomanage is not available (dnf plugin or standalone command)" >&2
  exit 1
fi

echo "Pruning repo root: $ROOT (keep=$KEEP dry_run=$DRY_RUN)"

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

  if [[ "$DRY_RUN" -eq 1 ]]; then
    for pkg in "${old_pkgs[@]}"; do
      echo "[DRY] $pkg"
    done
    continue
  fi

  for pkg in "${old_pkgs[@]}"; do
    rm -f -- "$pkg"
  done
  echo "[PRUNE] $dir (${#old_pkgs[@]} files removed)"

  if [[ -d "$dir/repodata" ]]; then
    "$CREATEREPO_BIN" --update "$dir" >/dev/null
    echo "[REPO]  $dir metadata updated"
  fi
done

echo "Done."
