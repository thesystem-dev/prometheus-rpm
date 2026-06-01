#!/usr/bin/env bash
set -euo pipefail

SCRIPT_NAME="$(basename "$0")"
INPUT_DIR="runtime/artifacts"
OUTPUT_DIR="runtime/repo"
RUNTIME_DIR="${RUNTIME_DIR:-runtime}"
PUBLIC_KEY_FILE="${PUBLIC_KEY_FILE:-}"
RPM_DB_DIR=""
SKIP_SIGNATURE_CHECK=false
ALLOW_UNSIGNED=false
RETAIN_OLD_MD_BY_AGE="2h"
RETENTION_EXPLICIT=false
NO_RETAIN_OLD_MD=false

usage() {
  cat <<EOF
Usage: $SCRIPT_NAME [options] [INPUT_DIR] [OUTPUT_DIR]

Create local DNF repository metadata from signed RPM artefacts.

Arguments:
  INPUT_DIR           RPM artefact tree (default: runtime/artifacts)
  OUTPUT_DIR          Repository output tree (default: runtime/repo)

Options:
  --public-key FILE   Public key used for rpm -K validation
                      (default: runtime/gnupg/public.asc or first
                      runtime/gnupg/RPM-GPG-KEY-*)
  --allow-unsigned    Local-only bypass: create repo metadata without rpm -K
                      signature validation
  --retain-old-md-by-age AGE
                      Retain old createrepo_c metadata for AGE
                      (default: 2h)
  --no-retain-old-md  Do not retain old repository metadata
  --runtime DIR       Runtime directory (default: runtime)
  -h, --help          Show this help text
EOF
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

warn() {
  echo "WARNING: $*" >&2
}

cleanup() {
  if [[ -n "$RPM_DB_DIR" && -d "$RPM_DB_DIR" ]]; then
    rm -rf "$RPM_DB_DIR"
  fi
}
trap cleanup EXIT

require_arg() {
  local option="$1"
  local value="${2:-}"
  [[ -n "$value" && "$value" != --* ]] || die "$option requires an argument"
}

positional=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --public-key)
      require_arg "$1" "${2:-}"
      PUBLIC_KEY_FILE="$2"
      shift 2
      ;;
    --public-key=*)
      PUBLIC_KEY_FILE="${1#*=}"
      [[ -n "$PUBLIC_KEY_FILE" ]] || die "--public-key requires an argument"
      shift
      ;;
    --allow-unsigned)
      ALLOW_UNSIGNED=true
      SKIP_SIGNATURE_CHECK=true
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
    --runtime)
      require_arg "$1" "${2:-}"
      RUNTIME_DIR="$2"
      shift 2
      ;;
    --runtime=*)
      RUNTIME_DIR="${1#*=}"
      [[ -n "$RUNTIME_DIR" ]] || die "--runtime requires an argument"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      while [[ $# -gt 0 ]]; do
        positional+=("$1")
        shift
      done
      ;;
    --*)
      usage >&2
      die "Unknown option: $1"
      ;;
    *)
      positional+=("$1")
      shift
      ;;
  esac
done

if [[ ${#positional[@]} -gt 2 ]]; then
  usage >&2
  die "Too many positional arguments"
fi
[[ ${#positional[@]} -ge 1 ]] && INPUT_DIR="${positional[0]}"
[[ ${#positional[@]} -ge 2 ]] && OUTPUT_DIR="${positional[1]}"

if [[ -d "$RUNTIME_DIR" ]]; then
  RUNTIME_DIR="$(cd "$RUNTIME_DIR" && pwd -P)"
else
  die "Runtime directory '$RUNTIME_DIR' not found (set RUNTIME_DIR to override)"
fi

if [[ ! -d "$INPUT_DIR" ]]; then
  die "Input directory '$INPUT_DIR' not found"
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
INPUT_ABS="$(cd "$INPUT_DIR" && pwd -P)"

resolve_output_path() {
  local output="$1"
  local parent
  local base

  if [[ -e "$output" ]]; then
    [[ -d "$output" ]] || die "Output path exists and is not a directory: $output"
    (cd "$output" && pwd -P)
    return
  fi

  parent="$(dirname "$output")"
  base="$(basename "$output")"
  [[ -d "$parent" ]] || die "Output parent directory not found: $parent"
  parent="$(cd "$parent" && pwd -P)"
  printf '%s/%s\n' "$parent" "$base"
}

path_is_within() {
  local child="$1"
  local parent="$2"
  [[ "$child" == "$parent"/* ]]
}

OUTPUT_ABS="$(resolve_output_path "$OUTPUT_DIR")"

validate_output_path() {
  [[ -n "$OUTPUT_ABS" ]] || die "Resolved output path is empty"
  [[ "$OUTPUT_ABS" != "/" ]] || die "Refusing to replace /"
  [[ "$OUTPUT_ABS" != "$ROOT_DIR" ]] || die "Refusing to replace repository root: $OUTPUT_ABS"
  [[ "$OUTPUT_ABS" != "$RUNTIME_DIR" ]] || die "Refusing to replace runtime directory: $OUTPUT_ABS"
  [[ "$OUTPUT_ABS" != "$INPUT_ABS" ]] || die "Output directory must differ from input directory"
  if path_is_within "$INPUT_ABS" "$OUTPUT_ABS"; then
    die "Refusing output directory that contains input directory: $OUTPUT_ABS"
  fi
  if path_is_within "$OUTPUT_ABS" "$INPUT_ABS"; then
    die "Refusing output directory inside input directory: $OUTPUT_ABS"
  fi
}

validate_output_path

GNUPG_DIR="$RUNTIME_DIR/gnupg"
if [[ "$SKIP_SIGNATURE_CHECK" != true && -z "$PUBLIC_KEY_FILE" ]]; then
  if [[ -d "$GNUPG_DIR" && -f "$GNUPG_DIR/public.asc" ]]; then
    PUBLIC_KEY_FILE="$GNUPG_DIR/public.asc"
  elif [[ -d "$GNUPG_DIR" ]]; then
    for key in "$GNUPG_DIR"/RPM-GPG-KEY-*; do
      if [[ -f "$key" ]]; then
        PUBLIC_KEY_FILE="$key"
        break
      fi
    done
  fi
fi

CREATEREPO_BIN=""
if command -v createrepo_c >/dev/null 2>&1; then
  CREATEREPO_BIN="createrepo_c"
elif command -v createrepo >/dev/null 2>&1; then
  CREATEREPO_BIN="createrepo"
else
  die "Neither createrepo_c nor createrepo is installed"
fi

if [[ "$CREATEREPO_BIN" != "createrepo_c" ]]; then
  if [[ "$RETENTION_EXPLICIT" == true && "$NO_RETAIN_OLD_MD" != true ]]; then
    die "--retain-old-md-by-age requires createrepo_c"
  fi
  if [[ "$NO_RETAIN_OLD_MD" != true ]]; then
    warn "createrepo_c not found; old metadata retention is unavailable with $CREATEREPO_BIN"
  fi
fi

if [[ "$ALLOW_UNSIGNED" == true ]]; then
  warn "--allow-unsigned set; rpm -K signature validation is disabled"
fi

copy_rpms() {
  local source_dir="$1"
  local target_dir="$2"
  local rpm_type="$3"

  if [[ "$rpm_type" == "source" ]]; then
    find "$source_dir" -type f -name "*.src.rpm" -print0 \
      | xargs -0r cp --preserve=mode,timestamps -t "$target_dir"
  else
    find "$source_dir" -type f -name "*.rpm" ! -name "*.src.rpm" -print0 \
      | xargs -0r cp --preserve=mode,timestamps -t "$target_dir"
  fi
}

sync_target_rpms() {
  local target_dir="$1"
  local rpm_type="$2"

  if [[ "$rpm_type" == "source" ]]; then
    find "$target_dir" -maxdepth 1 -type f -name "*.src.rpm" -delete
  else
    find "$target_dir" -maxdepth 1 -type f -name "*.rpm" ! -name "*.src.rpm" -delete
  fi
}

createrepo_update() {
  local target_dir="$1"
  local -a args=(--update)

  if [[ "$CREATEREPO_BIN" == "createrepo_c" && "$NO_RETAIN_OLD_MD" != true ]]; then
    args+=(--retain-old-md-by-age "$RETAIN_OLD_MD_BY_AGE")
  fi

  "$CREATEREPO_BIN" "${args[@]}" "$target_dir"
}

remove_target_dir() {
  local target_dir="$1"

  [[ "$target_dir" != "$OUTPUT_ABS" ]] || die "Refusing to remove output root: $target_dir"
  path_is_within "$target_dir" "$OUTPUT_ABS" || die "Refusing to remove path outside output root: $target_dir"
  rm -rf "$target_dir"
}

setup_rpm_db() {
  if [[ "$SKIP_SIGNATURE_CHECK" == true ]]; then
    return
  fi

  if [[ -z "$PUBLIC_KEY_FILE" ]]; then
    die "Public key not found under $GNUPG_DIR (use --public-key FILE or --allow-unsigned for local-only testing)"
  fi

  if [[ ! -f "$PUBLIC_KEY_FILE" ]]; then
    die "Public key file '$PUBLIC_KEY_FILE' not found or not readable"
  fi

  RPM_DB_DIR="$(mktemp -d)"
  if rpm --dbpath "$RPM_DB_DIR" --import "$PUBLIC_KEY_FILE" &>/dev/null; then
    echo "Imported public key from $PUBLIC_KEY_FILE for integrity checks"
  else
    rm -rf "$RPM_DB_DIR"
    RPM_DB_DIR=""
    die "Failed to import public key from $PUBLIC_KEY_FILE"
  fi
}

validate_rpms() {
  local target_dir="$1"
  local rpm_glob="$2"

  if [[ "$SKIP_SIGNATURE_CHECK" == true ]]; then
    echo "Skipping rpm -K validation for $target_dir (--allow-unsigned)"
    return
  fi

  local -a failed_rpms=()
  for rpm in "$target_dir"/$rpm_glob; do
    [[ -f "$rpm" ]] || continue
    if ! rpm --dbpath "$RPM_DB_DIR" -K "$rpm" >/dev/null 2>&1; then
      failed_rpms+=("$rpm")
    fi
  done

  if [[ ${#failed_rpms[@]} -gt 0 ]]; then
    echo "ERROR: RPM integrity check failed for:" >&2
    printf '  %s\n' "${failed_rpms[@]}" >&2
    die "Cannot proceed with unsigned, invalid, or untrusted RPMs"
  fi
}

setup_rpm_db
mkdir -p "$OUTPUT_ABS"

for distro_dir in "$INPUT_DIR"/el*; do
  [[ -d "$distro_dir" ]] || continue
  distro_name="$(basename "$distro_dir")"

  for arch_dir in "$distro_dir"/*; do
    [[ -d "$arch_dir" ]] || continue
    arch_name="$(basename "$arch_dir")"
    target_dir="$OUTPUT_ABS/$distro_name/$arch_name"
    mkdir -p "$target_dir"

    rpm_glob="*.rpm"
    rpm_label="RPMs"
    rpm_type="binary"
    if [[ "$arch_name" == "SRPMS" ]]; then
      rpm_glob="*.src.rpm"
      rpm_label="SRPMs"
      rpm_type="source"
    fi

    sync_target_rpms "$target_dir" "$rpm_type"
    copy_rpms "$arch_dir" "$target_dir" "$rpm_type"

    if compgen -G "$target_dir/$rpm_glob" >/dev/null; then
      # Validate RPM integrity before generating metadata
      echo "Validating $rpm_label integrity for $distro_name/$arch_name"
      validate_rpms "$target_dir" "$rpm_glob"

      echo "Generating repo metadata for $distro_name/$arch_name"
      createrepo_update "$target_dir"
    else
      echo "No $rpm_label found for $distro_name/$arch_name; removing empty directory"
      remove_target_dir "$target_dir"
    fi
  done
done

# Propagate noarch RPMs into both arch repos per EL so consumers on any arch
# can resolve them even if only one arch was built.
for distro_dir in "$OUTPUT_ABS"/el*; do
  [[ -d "$distro_dir" ]] || continue
  x_dir="$distro_dir/x86_64"
  a_dir="$distro_dir/aarch64"

  # Collect unique noarch RPMs already copied for this EL
  # They may originate from either arch's build output.
  mapfile -t noarch_rpms < <(find "$distro_dir" -type f -name "*.noarch.rpm" -print 2>/dev/null | sort -u)

  if [[ ${#noarch_rpms[@]} -gt 0 ]]; then
    mkdir -p "$x_dir" "$a_dir"

    echo "Ensuring noarch RPMs are available under both $distro_dir/x86_64 and $distro_dir/aarch64"
    for rpm in "${noarch_rpms[@]}"; do
      cp --preserve=mode,timestamps -n "$rpm" "$x_dir/" 2>/dev/null || true
      cp --preserve=mode,timestamps -n "$rpm" "$a_dir/" 2>/dev/null || true
    done

    # Refresh metadata after noarch propagation
    if compgen -G "$x_dir/*.rpm" >/dev/null; then
      echo "Updating metadata for ${distro_dir}/x86_64 (after noarch propagation)"
      createrepo_update "$x_dir"
    fi
    if compgen -G "$a_dir/*.rpm" >/dev/null; then
      echo "Updating metadata for ${distro_dir}/aarch64 (after noarch propagation)"
      createrepo_update "$a_dir"
    fi
  fi
done

echo "Repository content available in '$OUTPUT_ABS'"
