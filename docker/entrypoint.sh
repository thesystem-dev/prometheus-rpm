#!/usr/bin/env bash
set -e

# No args → interactive shell
if [[ $# -eq 0 ]]; then
  exec /bin/bash
fi

# `--` means bypass the build wrapper
if [[ "$1" == "--" ]]; then
  shift
  if [[ $# -eq 0 ]]; then
    exec /bin/bash
  fi
  exec "$@"
fi

# Allow explicit commands (e.g., ./scripts/create-repo.sh) without `--`
if [[ "$1" == */* ]] && [[ -e "$1" ]]; then
  exec "$@"
fi

# Otherwise pass through to build.sh
exec /home/builder/build.sh "$@"
