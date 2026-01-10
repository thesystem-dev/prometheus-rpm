#!/bin/sh
set -eu

RUNTIME_DIR="runtime"
TEMPLATES_DIR="templates"
RESULTS_DIR="runtime/artifacts"
REPO_DIR="runtime/repo"
SOURCES_DIR="sources"
KEY_ID=""
PACKAGER=""
FORCE=false
CHECK_SOURCES=false

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Prepare runtime directories and copy signing templates.

Options:
  --runtime <dir>     Target runtime directory (default: runtime)
  --templates <dir>   Source template directory (default: templates)
  --results <dir>     Results directory to create (default: runtime/artifacts)
  --repo <dir>        Repository directory to create (default: runtime/repo)
  --sources <dir>     Source directory for --check-sources (default: sources)
  --check-sources     Check for basename conflicts in sources/ (no staging)
  --key-id <id>       Override %_gpg_name in runtime/rpmmacros
  --packager <str>    Override %packager in runtime/rpmmacros
  --force             Overwrite runtime/rpmmacros even if it exists
  -h, --help          Show this help text
EOF
}

error() {
  echo "ERROR: $*" >&2
  exit 1
}

# Check for basename conflicts in source files (POSIX sh compatible)
# Returns 0 on success, 1 if conflicts detected
check_source_conflicts() {
  sources_dir="$1"
  
  if [ ! -d "$sources_dir" ]; then
    error "Sources directory not found: $sources_dir"
  fi
  
  # Find all source files and extract basenames
  tmpfile="$(mktemp)"
  find "$sources_dir" -mindepth 2 -type f -exec basename {} \; | sort > "$tmpfile"
  
  # Check for duplicates
  duplicates="$(uniq -d < "$tmpfile")"
  
  if [ -n "$duplicates" ]; then
    echo "ERROR: Basename conflicts detected:" >&2
    echo "$duplicates" | while IFS= read -r basename_file; do
      echo "  File: $basename_file" >&2
      echo "  Locations:" >&2
      find "$sources_dir" -mindepth 2 -name "$basename_file" -type f | sed 's/^/    /' >&2
    done
    rm -f "$tmpfile"
    return 1
  fi
  
  # Count files and packages
  file_count="$(wc -l < "$tmpfile" | tr -d ' ')"
  package_count="$(find "$sources_dir" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
  
  rm -f "$tmpfile"
  
  echo "Found $file_count source files across $package_count packages"
  return 0
}

while [ $# -gt 0 ]; do
  case "$1" in
    --runtime)
      RUNTIME_DIR="$2"
      shift 2
      ;;
    --templates)
      TEMPLATES_DIR="$2"
      shift 2
      ;;
    --results)
      RESULTS_DIR="$2"
      shift 2
      ;;
    --repo)
      REPO_DIR="$2"
      shift 2
      ;;
    --sources)
      SOURCES_DIR="$2"
      shift 2
      ;;
    --check-sources)
      CHECK_SOURCES=true
      shift
      ;;
    --key-id)
      KEY_ID="$2"
      shift 2
      ;;
    --packager)
      PACKAGER="$2"
      shift 2
      ;;
    --force)
      FORCE=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      error "Unknown option: $1"
      ;;
  esac
done

# Short-circuit for --check-sources mode (no staging operations)
if [ "$CHECK_SOURCES" = true ]; then
  echo "Checking source basename conflicts..."
  if check_source_conflicts "$SOURCES_DIR"; then
    echo "✓ No conflicts: all source basenames are unique"
    exit 0
  else
    echo "✗ Conflict detected (see above)" >&2
    exit 1
  fi
fi

[ -f "$TEMPLATES_DIR/rpmmacros" ] || error "Template '$TEMPLATES_DIR/rpmmacros' not found"

# Defensive check: validate source basenames before staging
echo "Validating source files..."
if ! check_source_conflicts "$SOURCES_DIR" > /dev/null 2>&1; then
  echo "ERROR: Source basename conflicts detected. Run with --check-sources for details." >&2
  exit 1
fi

mkdir -p "$RUNTIME_DIR" "$RUNTIME_DIR/SOURCES" "$RUNTIME_DIR/gnupg" "$RESULTS_DIR" "$REPO_DIR"
chmod 700 "$RUNTIME_DIR/gnupg"

MACROS_DEST="$RUNTIME_DIR/rpmmacros"
MACROS_TMP="$(mktemp)"

if [ -f "$MACROS_DEST" ] && [ "$FORCE" = false ]; then
  cp "$MACROS_DEST" "$MACROS_TMP"
else
  cp "$TEMPLATES_DIR/rpmmacros" "$MACROS_TMP"
fi

update_macro() {
  file="$1"
  key="$2"
  value="$3"
  tmp="$(mktemp)"
  if grep -q "^$key" "$file"; then
    awk -v key="$key" -v value="$value" '
      index($0, key) == 1 {print key " " value; next}
      {print}
    ' "$file" >"$tmp"
  else
    cat "$file" >"$tmp"
    printf '%s %s\n' "$key" "$value" >>"$tmp"
  fi
  mv "$tmp" "$file"
}

if [ -n "$KEY_ID" ]; then
  update_macro "$MACROS_TMP" "%_gpg_name" "$KEY_ID"
fi

if [ -n "$PACKAGER" ]; then
  update_macro "$MACROS_TMP" "%packager" "$PACKAGER"
fi

mv "$MACROS_TMP" "$MACROS_DEST"
chmod 600 "$MACROS_DEST"

cat <<EOF
Runtime prepared:
  Macros:    $MACROS_DEST
  GnuPG dir: $RUNTIME_DIR/gnupg
  Results:   $RESULTS_DIR
  Repo:      $REPO_DIR
EOF
