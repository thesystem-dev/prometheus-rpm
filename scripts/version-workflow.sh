#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
RUNTIME="$ROOT/runtime"
LOG_DIR="$RUNTIME/logs"
LOG_FILE=""
BUMP_SCRIPT="$RUNTIME/bump.sh"
PLAN_ONLY=false
SKIP_INVENTORY=false

cd "$ROOT"

usage() {
  cat <<'EOF'
Usage: ./scripts/version-workflow.sh [options]

Refresh upstream release metadata, spec version bumps, source checksums, and
the exporter inventory.

Options:
  --plan-only       Stop after discovery and bump planning
  --skip-inventory  Do not regenerate docs/exporters.md after checksum sync
  -h, --help        Show this help
EOF
}

stage() {
  if [[ -n "$LOG_FILE" ]]; then
    printf '\n==> %s\n' "$1" | tee -a "$LOG_FILE"
  else
    printf '\n==> %s\n' "$1"
  fi
}

run() {
  if [[ -n "$LOG_FILE" ]]; then
    {
      printf '+'
      printf ' %q' "$@"
      printf '\n'
    } | tee -a "$LOG_FILE"

    set +e
    "$@" 2>&1 | tee -a "$LOG_FILE"
    local status="${PIPESTATUS[0]}"
    set -e
    return "$status"
  fi

  printf '+'
  printf ' %q' "$@"
  printf '\n'
  "$@"
}

python_container() {
  run docker run --rm \
    -e GITHUB_TOKEN \
    -e GH_TOKEN \
    -e PIP_DISABLE_PIP_VERSION_CHECK=1 \
    -v "$ROOT:/work" \
    -w /work \
    python:3.14-slim \
    bash -lc "$1"
}

builder_container() {
  run docker run --rm \
    -v "$ROOT:/work" \
    -v "$RUNTIME/rpmmacros:/home/builder/.rpmmacros:ro" \
    -w /work \
    prometheus-rpm-builder:1.0 \
    "$@"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --plan-only)
      PLAN_ONLY=true
      shift
      ;;
    --skip-inventory)
      SKIP_INVENTORY=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      echo "ERROR: unknown option: $1" >&2
      exit 1
      ;;
  esac
done

mkdir -p "$RUNTIME" "$LOG_DIR"
LOG_FILE="$LOG_DIR/version-workflow-$(date +%Y%m%d-%H%M%S).log"
printf 'Logging to %s\n' "$LOG_FILE"
printf 'Log may contain sensitive output; do not share or commit it.\n'
{
  printf 'Logging to %s\n' "$LOG_FILE"
  printf 'Log may contain sensitive output; do not share or commit it.\n'
} >> "$LOG_FILE"

rm -f "$BUMP_SCRIPT"

stage "Discover upstream versions"
python_container \
  "pip install -r requirements.txt && python scripts/discover_versions.py > runtime/upstream-discovery.yaml"

stage "Plan spec version bumps"
python_container \
  "pip install -r requirements.txt && python scripts/plan-version-bumps.py --discover-cache runtime/upstream-discovery.yaml --write-script runtime/bump.sh"

if [[ "$PLAN_ONLY" == true ]]; then
  printf '\nPlan-only run complete. Review runtime/upstream-discovery.yaml and runtime/bump.sh if it was generated.\n'
  exit 0
fi

if [[ -f "$BUMP_SCRIPT" ]]; then
  if [[ ! -f "$RUNTIME/rpmmacros" ]]; then
    echo "ERROR: runtime/rpmmacros not found. Run ./scripts/stage-runtime.sh first." >&2
    exit 1
  fi
  stage "Apply spec version bumps"
  builder_container ./runtime/bump.sh
else
  printf '\nNo spec version bump script was generated; specs already match discovered versions.\n'
fi

stage "Sync source checksums"
python_container \
  "pip install -r requirements.txt && python scripts/sync-source-checksums.py --discover-cache runtime/upstream-discovery.yaml"

if [[ "$SKIP_INVENTORY" == false ]]; then
  stage "Regenerate exporter inventory"
  python_container \
    "pip install -r requirements.txt && python scripts/generate_exporter_inventory.py"
fi
