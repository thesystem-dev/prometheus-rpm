#!/usr/bin/env bash
set -euo pipefail

# RPM Signing Helper
# Signs RPMs using GPG keys staged in runtime/gnupg/

SCRIPT_NAME="$(basename "$0")"
RUNTIME_DIR="${RUNTIME_DIR:-runtime}"
INPUT_DIR="${INPUT_DIR:-}"
GNUPG_DIR=""
RPMMACROS=""
KEY_FILE=""
OWNERTRUST_FILE=""
LOG_FILE=""
PUBLIC_KEY_FILE=""
RPM_DB_DIR=""

# Signing configuration
MODE="sign"
FORCE=false
RPM_TYPES="both"
OUTPUT_DIR=""
IN_PLACE=true
INPUT_DIR_SET=false
if [[ -n "$INPUT_DIR" ]]; then
  INPUT_DIR_SET=true
fi

# Counters
SIGNED_COUNT=0
SKIPPED_COUNT=0
FAILED_COUNT=0
UNTRUSTED_COUNT=0

usage() {
  cat <<EOF
Usage: $SCRIPT_NAME [options]

Sign RPMs using GPG key material from runtime/gnupg/

Modes:
  (default)           Sign unsigned RPMs, skip already-signed
  --verify            Check signature status without signing
  --dry-run           Show what would be signed without making changes

Options:
  --force             Re-sign all RPMs (overwrite existing signatures)
  --rpm-types TYPE    Sign binary|source|both RPMs (default: both)
  --input-dir DIR     Input directory (default: <runtime>/artifacts)
  --output-dir DIR    Copy signed RPMs here (default: sign in-place)
  --runtime DIR       Runtime directory (default: runtime/)
  -h, --help          Show this help text

Environment Variables:
  GPG_PASSPHRASE      GPG key passphrase (prompts if not set)
  RUNTIME_DIR         Override default runtime directory

Examples:
  # Sign all unsigned RPMs (interactive passphrase prompt)
  $SCRIPT_NAME

  # Non-interactive signing (CI mode)
  GPG_PASSPHRASE='secret' $SCRIPT_NAME

  # Verify signatures
  $SCRIPT_NAME --verify

  # Force re-sign with output directory
  $SCRIPT_NAME --force --output-dir runtime/signed

  # Sign only binary RPMs
  $SCRIPT_NAME --rpm-types binary
EOF
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

log() {
  echo "$*" | tee -a "$LOG_FILE"
}

warn() {
  echo "WARNING: $*" >&2
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --verify)
      MODE="verify"
      shift
      ;;
    --dry-run)
      MODE="dry-run"
      shift
      ;;
    --force)
      FORCE=true
      shift
      ;;
    --rpm-types)
      RPM_TYPES="$2"
      shift 2
      ;;
    --input-dir)
      INPUT_DIR="$2"
      INPUT_DIR_SET=true
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      IN_PLACE=false
      shift 2
      ;;
    --runtime)
      RUNTIME_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      die "Unknown option: $1"
      ;;
  esac
done

# Normalise runtime path
if [[ -d "$RUNTIME_DIR" ]]; then
  RUNTIME_DIR="$(cd "$RUNTIME_DIR" && pwd)"
else
  die "Runtime directory not found: $RUNTIME_DIR"
fi

# Recompute derived paths after parsing (runtime may have changed via flags)
GNUPG_DIR="$RUNTIME_DIR/gnupg"
RPMMACROS="$RUNTIME_DIR/rpmmacros"
KEY_FILE="$GNUPG_DIR/private.asc"
OWNERTRUST_FILE="$GNUPG_DIR/ownertrust.txt"
LOG_FILE="$RUNTIME_DIR/artifacts/signing.log"
if [[ "$INPUT_DIR_SET" == false ]]; then
  INPUT_DIR="$RUNTIME_DIR/artifacts"
fi

# Locate a public key we can import for verification
if [[ -z "${PUBLIC_KEY_FILE:-}" ]]; then
  if [[ -f "$GNUPG_DIR/public.asc" ]]; then
    PUBLIC_KEY_FILE="$GNUPG_DIR/public.asc"
  else
    PUBLIC_KEY_FILE="$(ls "$GNUPG_DIR"/RPM-GPG-KEY-* 2>/dev/null | head -n1 || true)"
  fi
fi

# Validate RPM_TYPES
case "$RPM_TYPES" in
  binary|source|both)
    ;;
  *)
    die "Invalid --rpm-types value: $RPM_TYPES (must be: binary, source, or both)"
    ;;
esac

# Pre-flight checks
[[ -d "$INPUT_DIR" ]] || die "Input directory not found: $INPUT_DIR"
[[ -d "$GNUPG_DIR" ]] || die "GPG directory not found: $GNUPG_DIR (run scripts/stage-runtime.sh first)"
[[ -f "$KEY_FILE" ]] || die "GPG key file not found: $KEY_FILE"
[[ -f "$RPMMACROS" ]] || die "RPM macros file not found: $RPMMACROS"

# Extract GPG key ID from rpmmacros
if ! GPG_KEY_ID=$(grep '^%_gpg_name' "$RPMMACROS" | awk '{print $2}'); then
  die "Failed to extract %_gpg_name from $RPMMACROS"
fi
[[ -n "$GPG_KEY_ID" ]] || die "Empty %_gpg_name in $RPMMACROS"

# Ensure log directory exists before writing
mkdir -p "$(dirname "$LOG_FILE")"

log "=========================================="
log "RPM Signing - $(date)"
log "=========================================="
log "Mode: $MODE"
log "Input: $INPUT_DIR"
log "GPG Key ID: $GPG_KEY_ID"
log "RPM Types: $RPM_TYPES"
[[ "$FORCE" == true ]] && log "Force: enabled"
[[ "$IN_PLACE" == false ]] && log "Output: $OUTPUT_DIR"

# Find RPMs to process
find_rpms() {
  local input_dir="$1"
  local rpm_types="$2"
  
  case "$rpm_types" in
    binary)
      find "$input_dir" -type f -name "*.rpm" ! -name "*.src.rpm" 2>/dev/null || true
      ;;
    source)
      find "$input_dir" -type f -name "*.src.rpm" 2>/dev/null || true
      ;;
    both)
      find "$input_dir" -type f -name "*.rpm" 2>/dev/null || true
      ;;
  esac
}

mapfile -t RPMS < <(find_rpms "$INPUT_DIR" "$RPM_TYPES")

if [[ ${#RPMS[@]} -eq 0 ]]; then
  log "No RPMs found in $INPUT_DIR"
  exit 0
fi

log "Found ${#RPMS[@]} RPM(s) to process"

import_public_key() {
  local key_file="$1"
  [[ -n "$key_file" && -f "$key_file" ]] || return 0

  RPM_DB_DIR="$(mktemp -d)"

  local import_log
  import_log="$(mktemp)"
  if rpm --dbpath "$RPM_DB_DIR" --import "$key_file" &>"$import_log"; then
    log "Imported public key from $key_file into $RPM_DB_DIR"
  else
    warn "Failed to import public key from $key_file (verification may show SIGNED*)"
    while IFS= read -r line; do
      warn "  rpm: $line"
    done <"$import_log"
  fi
  rm -f "$import_log"
}

signature_status() {
  local rpm="$1"
  local output
  local db_args=()
  if [[ -n "$RPM_DB_DIR" && -d "$RPM_DB_DIR" ]]; then
    db_args=(--dbpath "$RPM_DB_DIR")
  fi
  output="$(rpm "${db_args[@]}" -Kv "$rpm" 2>&1 || true)"
  if [[ "$output" == *"Signature"* && "$output" == *"(none)"* ]]; then
    echo "unsigned"
    return 1
  fi
  if [[ "$output" == *"Signature"* ]]; then
    if [[ "$output" == *"NOKEY"* ]]; then
      echo "missing-key"
      return 0
    fi
    if [[ "$output" == *"NOT OK"* ]]; then
      echo "invalid"
      return 1
    fi
    echo "trusted"
    return 0
  fi
  # Fallback when rpm output is unexpected
  echo "unsigned"
  return 1
}

# Verify mode: just check signatures
if [[ "$MODE" == "verify" ]]; then
  log ""
  log "Verifying signatures..."
  log ""

  import_public_key "$PUBLIC_KEY_FILE"

  for rpm in "${RPMS[@]}"; do
    rpm_name="$(basename "$rpm")"
    sig_state="$(signature_status "$rpm")" || sig_state="invalid"
    case "$sig_state" in
      trusted)
        echo "[OK] SIGNED:      $rpm_name"
        ((++SIGNED_COUNT))
        ;;
      missing-key)
        echo "[?] SIGNED*:     $rpm_name (missing public key)"
        ((++UNTRUSTED_COUNT))
        ;;
      *)
        echo "[!!] UNSIGNED:    $rpm_name"
        ((++FAILED_COUNT))
        ;;
    esac
  done
  
  log ""
  log "Summary: ${SIGNED_COUNT} signed, ${UNTRUSTED_COUNT} signed (missing key), ${FAILED_COUNT} unsigned"
  if [[ $FAILED_COUNT -gt 0 ]]; then
    exit 1
  fi
  exit 0
fi

# Dry-run mode: show what would be done
if [[ "$MODE" == "dry-run" ]]; then
  log ""
  log "Dry-run mode (no changes will be made)..."
  log ""
  
  for rpm in "${RPMS[@]}"; do
    rpm_name="$(basename "$rpm")"
    sig_state="$(signature_status "$rpm")" || sig_state="invalid"
    if [[ "$sig_state" == "unsigned" || "$sig_state" == "invalid" ]]; then
      echo "[WOULD SIGN]    $rpm_name"
      ((++SIGNED_COUNT))
    else
      if [[ "$FORCE" == true ]]; then
        echo "[WOULD RE-SIGN] $rpm_name"
        ((++SIGNED_COUNT))
      else
        echo "[WOULD SKIP]    $rpm_name (already signed)"
        ((++SKIPPED_COUNT))
      fi
    fi
  done
  
  log ""
  log "Summary: ${SIGNED_COUNT} would be signed, ${SKIPPED_COUNT} would be skipped"
  exit 0
fi

# Sign mode: set up GPG and sign RPMs
log ""
log "Setting up GPG environment..."

# Create ephemeral GNUPGHOME
TEMP_GNUPGHOME="$(mktemp -d)"
export GNUPGHOME="$TEMP_GNUPGHOME"
chmod 700 "$GNUPGHOME"

cleanup_gpg() {
  if [[ -d "$TEMP_GNUPGHOME" ]]; then
    rm -rf "$TEMP_GNUPGHOME"
  fi
}
trap cleanup_gpg EXIT

# Import GPG key
log "Importing GPG key from $KEY_FILE..."
if ! gpg --batch --import "$KEY_FILE" &>/dev/null; then
  die "Failed to import GPG key from $KEY_FILE"
fi

# Import ownertrust if present
if [[ -f "$OWNERTRUST_FILE" ]]; then
  log "Importing ownertrust from $OWNERTRUST_FILE..."
  if ! gpg --import-ownertrust "$OWNERTRUST_FILE" &>/dev/null; then
    warn "Failed to import ownertrust (continuing anyway)"
  fi
fi

# Set ultimate trust for the key
echo "$GPG_KEY_ID:6:" | gpg --import-ownertrust &>/dev/null || true

# Verify key is usable
if ! gpg --list-secret-keys "$GPG_KEY_ID" &>/dev/null; then
  die "GPG key $GPG_KEY_ID not found in keyring after import"
fi

log "GPG key imported successfully"

# Handle passphrase
if [[ -z "${GPG_PASSPHRASE:-}" ]]; then
  # Interactive mode: check if we have a TTY
  if [[ ! -t 0 ]]; then
    die "GPG_PASSPHRASE not set and no TTY available for interactive prompt"
  fi

  log ""
  log "GPG_PASSPHRASE not set - using interactive pinentry prompts"
  log ""

  USE_EXPECT=false
else
  # Non-interactive mode with expect
  log "Using GPG_PASSPHRASE from environment"
  
  # Test passphrase
  if ! gpg --batch --pinentry-mode loopback --passphrase-fd 3 --armor --detach-sign --local-user "$GPG_KEY_ID" -o /dev/null 3<<<"$GPG_PASSPHRASE" <<<"test" &>/dev/null; then
    die "Invalid GPG_PASSPHRASE"
  fi
  
  USE_EXPECT=true
fi

# Create output directory if needed
if [[ "$IN_PLACE" == false ]]; then
  mkdir -p "$OUTPUT_DIR"
  log "Output directory: $OUTPUT_DIR"
fi

# Sign RPMs
log ""
log "Signing RPMs..."
log ""

sign_rpm() {
  local rpm="$1"
  local rpm_name="$(basename "$rpm")"
  local target_rpm="$rpm"
  local sig_state
  sig_state="$(signature_status "$rpm")" || sig_state="invalid"

  # Copy to output directory if needed
  if [[ "$IN_PLACE" == false ]]; then
    # Preserve directory structure
    local rel_path="${rpm#$INPUT_DIR/}"
    local target_dir="$OUTPUT_DIR/$(dirname "$rel_path")"
    mkdir -p "$target_dir"
    target_rpm="$target_dir/$(basename "$rpm")"
    cp "$rpm" "$target_rpm"
  fi

  # Skip already-signed RPMs unless forcing
  if [[ "$sig_state" != "unsigned" && "$sig_state" != "invalid" && "$FORCE" != true ]]; then
    echo "SKIP:    $rpm_name (already signed)"
    ((++SKIPPED_COUNT))
    return 0
  fi

  # Sign the RPM
  if [[ "$USE_EXPECT" == true ]]; then
    # Non-interactive signing with expect
    if expect -c "
      set timeout 30
      spawn rpmsign --addsign --define \"%_gpg_name $GPG_KEY_ID\" \"$target_rpm\"
      expect {
        \"Enter pass phrase:\" {
          send \"$GPG_PASSPHRASE\r\"
          exp_continue
        }
        eof
      }
    " &>/dev/null; then
      echo "SUCCESS: $rpm_name"
      ((++SIGNED_COUNT))
      return 0
    else
      echo "FAIL:    $rpm_name"
      ((++FAILED_COUNT))
      return 1
    fi
  else
    # Interactive signing
    if rpmsign --addsign --define "%_gpg_name $GPG_KEY_ID" "$target_rpm" &>/dev/null; then
      echo "SUCCESS: $rpm_name"
      ((++SIGNED_COUNT))
      return 0
    else
      echo "FAIL:    $rpm_name"
      ((++FAILED_COUNT))
      return 1
    fi
  fi
}

# Process each RPM
for rpm in "${RPMS[@]}"; do
  sign_rpm "$rpm" || true
done

# Summary
log ""
log "=========================================="
log "Signing complete"
log "=========================================="
log "Signed:  $SIGNED_COUNT"
log "Skipped: $SKIPPED_COUNT"
log "Failed:  $FAILED_COUNT"
log ""

if [[ -n "${RPM_DB_DIR:-}" && -d "$RPM_DB_DIR" ]]; then
  rm -rf "$RPM_DB_DIR"
fi

if [[ $FAILED_COUNT -gt 0 ]]; then
  die "Some RPMs failed to sign (see above)"
fi

exit 0
