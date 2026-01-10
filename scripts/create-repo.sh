#!/usr/bin/env bash
set -euo pipefail

INPUT_DIR="${1:-runtime/artifacts}"
OUTPUT_DIR="${2:-runtime/repo}"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

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

validate_rpms() {
  local target_dir="$1"
  local rpm_glob="$2"

  local -a failed_rpms=()
  for rpm in "$target_dir"/$rpm_glob; do
    [[ -f "$rpm" ]] || continue
    if ! rpm -K "$rpm" >/dev/null 2>&1; then
      failed_rpms+=("$rpm")
    fi
  done

  if [[ ${#failed_rpms[@]} -gt 0 ]]; then
    echo "ERROR: RPM integrity check failed for:" >&2
    printf '  %s\n' "${failed_rpms[@]}" >&2
    die "Cannot proceed with corrupted RPMs"
  fi
}

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

echo "Repository content available in '$OUTPUT_DIR'"
