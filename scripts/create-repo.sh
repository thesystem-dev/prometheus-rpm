#!/usr/bin/env bash
set -euo pipefail

INPUT_DIR="${1:-runtime/artifacts}"
OUTPUT_DIR="${2:-runtime/repo}"
RUNTIME_DIR="${RUNTIME_DIR:-runtime}"
PUBLIC_KEY_FILE="${PUBLIC_KEY_FILE:-}"
RPM_DB_DIR=""
SKIP_SIGNATURE_CHECK=false

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

if [[ -d "$RUNTIME_DIR" ]]; then
  RUNTIME_DIR="$(cd "$RUNTIME_DIR" && pwd)"
else
  die "Runtime directory '$RUNTIME_DIR' not found (set RUNTIME_DIR to override)"
fi

GNUPG_DIR="$RUNTIME_DIR/gnupg"
if [[ -z "$PUBLIC_KEY_FILE" ]]; then
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

if [[ -z "$PUBLIC_KEY_FILE" ]]; then
  warn "Public key not found under $GNUPG_DIR (signature validation will be skipped)"
  SKIP_SIGNATURE_CHECK=true
fi

if [[ ! -d "$INPUT_DIR" ]]; then
  die "Input directory '$INPUT_DIR' not found"
fi

CREATEREPO_BIN=""
if command -v createrepo_c >/dev/null 2>&1; then
  CREATEREPO_BIN="createrepo_c"
elif command -v createrepo >/dev/null 2>&1; then
  CREATEREPO_BIN="createrepo"
else
  die "Neither createrepo_c nor createrepo is installed"
fi

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

copy_rpms() {
  local source_dir="$1"
  local target_dir="$2"
  local rpm_type="$3"

  if [[ "$rpm_type" == "source" ]]; then
    find "$source_dir" -type f -name "*.src.rpm" -print0 \
      | xargs -0r cp -t "$target_dir"
  else
    find "$source_dir" -type f -name "*.rpm" ! -name "*.src.rpm" -print0 \
      | xargs -0r cp -t "$target_dir"
  fi
}

setup_rpm_db() {
  if [[ "$SKIP_SIGNATURE_CHECK" == true ]]; then
    return
  fi

  if [[ ! -f "$PUBLIC_KEY_FILE" ]]; then
    warn "Public key file '$PUBLIC_KEY_FILE' not found or not readable (skipping rpm -K validation)"
    SKIP_SIGNATURE_CHECK=true
    return
  fi

  RPM_DB_DIR="$(mktemp -d)"
  if rpm --dbpath "$RPM_DB_DIR" --import "$PUBLIC_KEY_FILE" &>/dev/null; then
    echo "Imported public key from $PUBLIC_KEY_FILE for integrity checks"
  else
    warn "Failed to import public key from $PUBLIC_KEY_FILE (skipping rpm -K validation)"
    rm -rf "$RPM_DB_DIR"
    RPM_DB_DIR=""
    SKIP_SIGNATURE_CHECK=true
  fi
}

validate_rpms() {
  local target_dir="$1"
  local rpm_glob="$2"

  if [[ "$SKIP_SIGNATURE_CHECK" == true ]]; then
    echo "Skipping rpm -K validation for $target_dir (no public key available)"
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
    die "Cannot proceed with corrupted RPMs"
  fi
}

setup_rpm_db

for distro_dir in "$INPUT_DIR"/el*; do
  [[ -d "$distro_dir" ]] || continue
  distro_name="$(basename "$distro_dir")"

  for arch_dir in "$distro_dir"/*; do
    [[ -d "$arch_dir" ]] || continue
    arch_name="$(basename "$arch_dir")"
    target_dir="$OUTPUT_DIR/$distro_name/$arch_name"
    mkdir -p "$target_dir"

    rpm_glob="*.rpm"
    rpm_label="RPMs"
    rpm_type="binary"
    if [[ "$arch_name" == "SRPMS" ]]; then
      rpm_glob="*.src.rpm"
      rpm_label="SRPMs"
      rpm_type="source"
    fi

    copy_rpms "$arch_dir" "$target_dir" "$rpm_type"

    if compgen -G "$target_dir/$rpm_glob" >/dev/null; then
      # Validate RPM integrity before generating metadata
      echo "Validating $rpm_label integrity for $distro_name/$arch_name"
      validate_rpms "$target_dir" "$rpm_glob"

      echo "Generating repo metadata for $distro_name/$arch_name"
      "$CREATEREPO_BIN" --update "$target_dir"
    else
      echo "No $rpm_label found for $distro_name/$arch_name; removing empty directory"
      rmdir "$target_dir"
    fi
  done
done

# Propagate noarch RPMs into both arch repos per EL so consumers on any arch
# can resolve them even if only one arch was built.
for distro_dir in "$OUTPUT_DIR"/el*; do
  [[ -d "$distro_dir" ]] || continue
  x_dir="$distro_dir/x86_64"
  a_dir="$distro_dir/aarch64"
  mkdir -p "$x_dir" "$a_dir"

  # Collect unique noarch RPMs already copied for this EL
  # They may originate from either arch's build output.
  mapfile -t noarch_rpms < <(find "$distro_dir" -type f -name "*.noarch.rpm" -print 2>/dev/null | sort -u)

  if [[ ${#noarch_rpms[@]} -gt 0 ]]; then
    echo "Ensuring noarch RPMs are available under both $distro_dir/x86_64 and $distro_dir/aarch64"
    for rpm in "${noarch_rpms[@]}"; do
      cp -n "$rpm" "$x_dir/" 2>/dev/null || true
      cp -n "$rpm" "$a_dir/" 2>/dev/null || true
    done

    # Refresh metadata after noarch propagation
    if compgen -G "$x_dir/*.rpm" >/dev/null; then
      echo "Updating metadata for ${distro_dir}/x86_64 (after noarch propagation)"
      "$CREATEREPO_BIN" --update "$x_dir"
    fi
    if compgen -G "$a_dir/*.rpm" >/dev/null; then
      echo "Updating metadata for ${distro_dir}/aarch64 (after noarch propagation)"
      "$CREATEREPO_BIN" --update "$a_dir"
    fi
  fi
done

echo "Repository content available in '$OUTPUT_DIR'"
