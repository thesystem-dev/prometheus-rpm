#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"

usage() {
  cat <<'EOF'
Usage: ./scripts/package-workflow.sh <stage> [stage args...]

Stages:
  build   Build RPMs with the Docker builder service
  sign    Sign built RPMs with the Docker signing service
  verify  Verify RPM signatures with the Docker signing service
  repo    Create the local DNF repository tree with the Docker builder service
  prune   Prune old RPMs from runtime/repo or runtime/artifacts

Requirements:
  build   runtime/ prepared by ./scripts/stage-runtime.sh
  sign    runtime/gnupg/private.asc and runtime/rpmmacros
  verify  runtime/artifacts plus staged public key material
  repo    runtime/artifacts plus staged public key material
  prune   runtime/repo or the selected --root path exists

Examples:
  ./scripts/package-workflow.sh build --all --el 9 --arch x86_64
  ./scripts/package-workflow.sh sign
  ./scripts/package-workflow.sh verify
  ./scripts/package-workflow.sh repo
  ./scripts/package-workflow.sh prune --dry-run
EOF
}

stage() {
  printf '\n==> %s\n' "$1"
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

require_file() {
  [[ -f "$1" ]] || die "$2"
}

require_dir() {
  [[ -d "$1" ]] || die "$2"
}

require_docker() {
  command -v docker >/dev/null 2>&1 || die "docker is required"
  [[ -f docker/docker-compose.yml ]] || die "docker/docker-compose.yml not found"
}

require_runtime() {
  require_dir runtime "runtime/ not found; run ./scripts/stage-runtime.sh first"
}

require_build_runtime() {
  require_runtime
  require_dir runtime/SOURCES "runtime/SOURCES not found; run ./scripts/stage-runtime.sh first"
  require_dir runtime/artifacts "runtime/artifacts not found; run ./scripts/stage-runtime.sh first"
}

require_signing_material() {
  require_runtime
  require_dir runtime/gnupg "runtime/gnupg not found; run ./scripts/stage-runtime.sh first"
  require_file runtime/gnupg/private.asc "runtime/gnupg/private.asc not found; export the private signing key first"
  require_file runtime/rpmmacros "runtime/rpmmacros not found; run ./scripts/stage-runtime.sh first"
}

require_public_key_material() {
  require_runtime
  require_dir runtime/gnupg "runtime/gnupg not found; run ./scripts/stage-runtime.sh first"
  if [[ -f runtime/gnupg/public.asc ]]; then
    return
  fi
  compgen -G "runtime/gnupg/RPM-GPG-KEY-*" >/dev/null || die "public GPG key not found under runtime/gnupg"
}

has_public_key_arg() {
  for arg in "$@"; do
    [[ "$arg" == "--public-key" ]] && return 0
  done
  return 1
}

require_artifacts() {
  require_dir runtime/artifacts "runtime/artifacts not found; build packages first"
}

run() {
  printf '+'
  printf ' %q' "$@"
  printf '\n'
  "$@"
}

if [[ $# -eq 0 ]]; then
  usage
  exit 1
fi

COMMAND="$1"
shift

case "$COMMAND" in
  build)
    require_docker
    require_build_runtime
    stage "Build RPMs"
    run docker compose -f docker/docker-compose.yml run --rm builder "$@"
    ;;
  sign)
    require_docker
    require_artifacts
    require_signing_material
    stage "Sign RPMs"
    compose_args=(docker compose -f docker/docker-compose.yml run --rm)
    if [[ -n "${GPG_PASSPHRASE:-}" ]]; then
      compose_args+=(-e GPG_PASSPHRASE)
    fi
    run "${compose_args[@]}" sign "$@"
    ;;
  verify)
    require_docker
    require_artifacts
    if ! has_public_key_arg "$@"; then
      require_public_key_material
    fi
    stage "Verify RPM signatures"
    run docker compose -f docker/docker-compose.yml run --rm sign --verify "$@"
    ;;
  repo)
    require_docker
    require_artifacts
    require_public_key_material
    stage "Create local DNF repository tree"
    run docker compose -f docker/docker-compose.yml run --rm builder ./scripts/create-repo.sh "$@"
    ;;
  prune)
    require_docker
    require_runtime
    stage "Prune old RPMs"
    run docker compose -f docker/docker-compose.yml run --rm builder ./scripts/prune-repo.sh "$@"
    ;;
  -h|--help)
    usage
    ;;
  *)
    usage >&2
    echo "ERROR: unknown stage: $COMMAND" >&2
    exit 1
    ;;
esac
