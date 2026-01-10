#!/usr/bin/env bash
set -euo pipefail

SPECS_DIR="$HOME/rpmbuild/SPECS"
SOURCES_DIR="$HOME/rpmbuild/SOURCES"
RESULTS_DIR="$HOME/rpmbuild/results"

usage() {
  cat <<EOF
Usage: build.sh [options]

Options:
  --all                  Build all packages
  --package <name>       Build specific package (repeatable)
  --el <8|9|10>          Target EL version (repeatable)
  --arch <x86_64|aarch64> Target architecture (repeatable)
  --list                 List available packages
  --check-sources        Check for basename conflicts only (no build)
  --dry-run              Show what would be built
  -h, --help             This help
EOF
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

command -v mock >/dev/null || die "mock not installed"
command -v spectool >/dev/null || die "spectool not installed"

# -------------------------
# Defaults
# -------------------------
PACKAGES=()
ELS=()
ARCHES=()
BUILD_ALL=false
DRY_RUN=false
CHECK_SOURCES=false

# -------------------------
# Argument parsing
# -------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)
      BUILD_ALL=true
      shift
      ;;
    --package)
      PACKAGES+=("$2")
      shift 2
      ;;
    --el)
      ELS+=("$2")
      shift 2
      ;;
    --arch)
      ARCHES+=("$2")
      shift 2
      ;;
    --list)
      ls "$SPECS_DIR"/*.spec | xargs -n1 basename | sed 's/\.spec$//'
      exit 0
      ;;
    --check-sources)
      CHECK_SOURCES=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown option: $1"
      ;;
  esac
done

# Short-circuit for --check-sources mode (no build operations)
if [[ "$CHECK_SOURCES" == true ]]; then
  CONFIGS_DIR="$HOME/configs"
  
  if [[ ! -d "$CONFIGS_DIR" ]]; then
    echo "ERROR: CONFIGS_DIR not set or does not exist: $CONFIGS_DIR" >&2
    echo "  (mount ./sources at $HOME/configs)" >&2
    exit 1
  fi
  
  echo "Checking source basename conflicts..."
  if check_source_conflicts "$CONFIGS_DIR"; then
    echo "✓ No conflicts: all source basenames are unique"
    exit 0
  else
    echo "✗ Conflict detected (see above)" >&2
    exit 1
  fi
fi

if [[ $# -eq 0 ]] && ! $BUILD_ALL && [[ ${#PACKAGES[@]} -eq 0 ]]; then
  usage
  exit 0
fi

# -------------------------
# Package selection
# -------------------------
if $BUILD_ALL; then
  mapfile -t PACKAGES < <(ls "$SPECS_DIR"/*.spec | xargs -n1 basename | sed 's/\.spec$//')
fi

# -------------------------
# EL defaults
# -------------------------
if [[ ${#ELS[@]} -eq 0 ]]; then
  ELS=(8 9 10)
fi

# -------------------------
# Arch defaults (host arch)
# -------------------------
if [[ ${#ARCHES[@]} -eq 0 ]]; then
  ARCHES=("$(uname -m)")
fi

# -------------------------
# EL → mock root mapping
# -------------------------
mock_root_for() {
  local el="$1"
  local arch="$2"

  case "$el" in
    8)
      echo "rocky-8-${arch}"
      ;;
    9)
      echo "almalinux-9-${arch}"
      ;;
    10)
      echo "almalinux-10-${arch}"
      ;;
    *)
      die "Unsupported EL version: $el"
      ;;
  esac
}

mkdir -p "$RESULTS_DIR"

# Stage static sources (tracked configs) into SOURCES alongside spectool downloads
if [[ -d "$SOURCES_DIR" ]]; then
  rm -rf "$SOURCES_DIR"/*
else
  mkdir -p "$SOURCES_DIR"
fi

CONFIGS_DIR="$HOME/configs"
if [[ ! -d "$CONFIGS_DIR" ]]; then
  die "Missing static sources directory '$CONFIGS_DIR' (bind-mount repo sources/ there)"
fi

# Verify we have at least some package subdirectories
if [[ -z "$(find "$CONFIGS_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null)" ]]; then
  die "Static sources directory '$CONFIGS_DIR' contains no package subdirectories (did you mount ./sources?)"
fi

# Check for basename conflicts in source files
# Returns 0 on success, 1 if conflicts detected
check_source_conflicts() {
  local configs_dir="$1"
  
  declare -A basename_sources
  local has_conflict=false
  
  while IFS= read -r -d '' source_file; do
    basename_file=$(basename "$source_file")
    
    if [[ -n "${basename_sources[$basename_file]:-}" ]]; then
      echo "ERROR: Basename conflict detected" >&2
      echo "  File: $basename_file" >&2
      echo "  Locations:" >&2
      echo "    ${basename_sources[$basename_file]}" >&2
      echo "    $source_file" >&2
      has_conflict=true
    fi
    
    basename_sources["$basename_file"]="$source_file"
  done < <(find "$configs_dir" -mindepth 2 -type f -print0)
  
  if [[ "$has_conflict" == true ]]; then
    return 1
  fi
  
  local file_count="${#basename_sources[@]}"
  local package_count=$(find "$configs_dir" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
  echo "Found $file_count source files across $package_count packages"
  
  return 0
}

# Function to flatten source files for rpmbuild resolution
# RPM cannot reliably resolve subdirectory paths in Source directives,
# so we must copy all files to $SOURCES_DIR root by basename
flatten_sources() {
  local configs_dir="$1"
  local sources_dir="$2"
  
  echo "Flattening source files for rpmbuild..."
  
  # Check for conflicts first
  if ! check_source_conflicts "$configs_dir" >/dev/null; then
    die "Basename conflicts detected (see above)"
  fi
  
  # Build file list for copying (conflicts already checked)
  declare -A basename_sources
  while IFS= read -r -d '' source_file; do
    basename_file=$(basename "$source_file")
    basename_sources["$basename_file"]="$source_file"
  done < <(find "$configs_dir" -mindepth 2 -type f -print0)
  
  # Now copy each file to SOURCES root
  for basename_file in "${!basename_sources[@]}"; do
    source_file="${basename_sources[$basename_file]}"
    cp "$source_file" "$sources_dir/$basename_file"
  done
  
  echo "Source files flattened: $(find "$sources_dir" -maxdepth 1 -type f | wc -l | tr -d ' ')"
}

echo "Staging package sources from $CONFIGS_DIR (per-package layout)..."

# Copy subdirectory structure for inspection/debugging
cp -a "$CONFIGS_DIR"/. "$SOURCES_DIR"/

# Flatten sources to SOURCES root
flatten_sources "$CONFIGS_DIR" "$SOURCES_DIR"

declare -A SOURCES_FETCHED=()

ensure_sources_for_arch() {
  local pkg="$1"
  local arch="$2"
  local spec="$3"
  local key="${pkg}_${arch}"

  if [[ -n "${SOURCES_FETCHED[$key]:-}" ]]; then
    return
  fi

  echo "Downloading sources for ${pkg} (${arch})..."
  spectool \
    --get-files \
    --sources \
    --directory "$SOURCES_DIR" \
    --define "_target_cpu $arch" \
    --define "_arch $arch" \
    "$spec"

  # spectool can clobber local files if it stages Source1+,
  # so re-copy and re-flatten the tracked configs after each fetch.
  cp -a "$CONFIGS_DIR"/. "$SOURCES_DIR"/
  flatten_sources "$CONFIGS_DIR" "$SOURCES_DIR"

  SOURCES_FETCHED["$key"]=1
}

# -------------------------
# Build loop
# -------------------------
for pkg in "${PACKAGES[@]}"; do
  spec="$SPECS_DIR/$pkg.spec"
  [[ -f "$spec" ]] || die "Missing spec: $spec"

  echo
  echo "============================================================"
  echo "Package: $pkg"
  echo "============================================================"
  for el in "${ELS[@]}"; do
    for arch in "${ARCHES[@]}"; do
      ensure_sources_for_arch "$pkg" "$arch" "$spec"

      mock_root="$(mock_root_for "$el" "$arch")"
      result_dir="$RESULTS_DIR/el${el}/${arch}"

      echo
      echo "------------------------------------------------------------"
      echo "Target: EL${el} / ${arch}"
      echo "Mock cfg: ${mock_root}"
      echo "------------------------------------------------------------"

      if $DRY_RUN; then
        echo "[DRY-RUN] mock -r ${mock_root} --buildsrpm ..."
        echo "[DRY-RUN] mock -r ${mock_root} --rebuild ..."
        continue
      fi

      mkdir -p "$result_dir"

      echo "Staged sources directory contents:"
      ls -al "$SOURCES_DIR"

      # Validate mock root exists
      if ! mock -r "$mock_root" --print-root-path >/dev/null 2>&1; then
        die "Mock root '$mock_root' not found. Install with: mock -r $mock_root --init"
      fi

      # Build SRPM with error capture
      build_log="$result_dir/build.log"
      if ! mock \
        -r "$mock_root" \
        --clean \
        --buildsrpm \
        --spec "$spec" \
        --sources "$SOURCES_DIR" \
        --resultdir "$result_dir" \
        2>&1 | tee "$build_log"; then
        die "SRPM build failed for $pkg (EL${el}/${arch}). See: $build_log"
      fi

      # Validate SRPM was produced
      srpms=("$result_dir"/*.src.rpm)
      if [[ ! -e "${srpms[0]}" ]]; then
        die "No SRPM produced for $pkg (EL${el}/${arch})"
      fi
      if [[ ${#srpms[@]} -gt 1 ]]; then
        die "Multiple SRPMs found for $pkg (EL${el}/${arch}): ${srpms[*]}"
      fi
      srpm="${srpms[0]}"

      # Rebuild RPM with error capture
      if ! mock \
        -r "$mock_root" \
        --rebuild "$srpm" \
        --resultdir "$result_dir" \
        2>&1 | tee -a "$build_log"; then
        die "RPM rebuild failed for $pkg (EL${el}/${arch}). See: $build_log"
      fi

      srpm_dir="$RESULTS_DIR/el${el}/SRPMS"
      mkdir -p "$srpm_dir"
      for srpm_file in "$result_dir"/*.src.rpm; do
        [[ -e "$srpm_file" ]] || break
        mv "$srpm_file" "$srpm_dir/"
      done
    done
  done
done

echo
echo "============================================================"
echo "Builds completed"
echo "============================================================"
