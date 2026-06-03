# Maintainer Commands

This page is the short path for day-to-day repository maintenance. These commands call the existing helpers and Docker services; they do not replace the lower-level scripts.

Run commands from the repository root.

## Version refresh

Prerequisites:

- Docker must be available.
- `GITHUB_TOKEN` or `GH_TOKEN` is recommended for GitHub API rate limits; see [version-tracking.md](version-tracking.md).
- Run `./scripts/stage-runtime.sh --key-id <GPG_KEY> --packager "Name <email>"` before applying version bumps, because bump application uses `runtime/rpmmacros`; see [runtime.md](runtime.md).

Refresh upstream release data, apply spec version bumps, sync source checksums, and regenerate the exporter inventory:

```bash
./scripts/version-workflow.sh
```

Supported options:

| Option | Effect |
| --- | --- |
| `--plan-only` | Discover upstream releases, write `runtime/upstream-discovery.yaml`, write `runtime/bump.sh` if bumps are needed, then stop. |
| `--skip-inventory` | Run discovery, bump planning/application, and checksum sync, but do not regenerate `docs/exporters.md`. |
| `-h`, `--help` | Show help. |

Plan only:

```bash
./scripts/version-workflow.sh --plan-only
```

This discovers upstream releases and writes the bump plan under `runtime/`, then stops. It does not apply spec version bumps, sync checksum data, or regenerate `docs/exporters.md`.

Refresh without regenerating `docs/exporters.md`:

```bash
./scripts/version-workflow.sh --skip-inventory
```

This command writes generated state under `runtime/` and may modify tracked files:

- `upstreams.yaml`
- `specs/*.spec`
- `docs/exporters.md`

Each run also writes a timestamped log under `runtime/logs/`. The log is useful for reviewing Docker and helper output, but it may contain sensitive output from child commands.

Review the diff before committing. See [version-tracking.md](version-tracking.md) for the underlying helper scripts and upstream metadata rules.

## Package maintenance

Prepare the runtime tree before package stages:

```bash
./scripts/stage-runtime.sh --key-id <GPG_KEY> --packager "Name <email>"
```

Stage requirements:

| Stage | Required before running |
| --- | --- |
| `build` | Docker Compose and `runtime/` prepared by `stage-runtime.sh`; see [runtime.md](runtime.md) and [build-and-stage.md](build-and-stage.md) |
| `sign` | Built RPMs under `runtime/artifacts/`, `runtime/gnupg/private.asc`, and `runtime/rpmmacros`; see [signing.md](signing.md) |
| `verify` | Built RPMs under `runtime/artifacts/` plus a public key under `runtime/gnupg/public.asc` or `runtime/gnupg/RPM-GPG-KEY-*`; private key material is not required; see [signing.md](signing.md) |
| `repo` | Built RPMs under `runtime/artifacts/` plus a public key under `runtime/gnupg/public.asc` or `runtime/gnupg/RPM-GPG-KEY-*`, unless using the explicit local-only `--allow-unsigned` bypass; see [publishing.md](publishing.md) |
| `prune` | Existing `runtime/repo` or the selected `--root` path; dry-run first; see [publishing.md](publishing.md) |

Environment:

| Variable | Used by | Required |
| --- | --- | --- |
| `GPG_PASSPHRASE` | `sign` | Required for non-interactive/headless signing. If unset, `scripts/sign-rpms.sh` may prompt interactively when a TTY is available. |

Build RPMs:

```bash
./scripts/package-workflow.sh build --all --el 9 --arch x86_64 --arch aarch64
```

Build selected packages:

```bash
./scripts/package-workflow.sh build --package prometheus --package node_exporter --el 9 --arch x86_64
```

For `BuildArch: noarch` packages, one architecture is enough per EL release. Repository creation copies noarch RPMs into both architecture trees.

Sign built RPMs:

```bash
export GPG_PASSPHRASE="..."
./scripts/package-workflow.sh sign
```

Verify signatures:

```bash
./scripts/package-workflow.sh verify
```

Create the local repository:

```bash
./scripts/package-workflow.sh repo
```

This creates the local DNF repository tree under `runtime/repo/` by copying RPMs from `runtime/artifacts/` and generating `repodata/`. It does not publish or upload the repository.

Repository creation validates copied RPMs with the staged public key and fails closed if validation cannot run. Use `--allow-unsigned` only for local throwaway testing.

Dry-run pruning before deleting old RPMs:

```bash
./scripts/package-workflow.sh prune --root runtime/repo --keep 3 --dry-run
```

Supported stages and arguments:

| Stage | Arguments passed through |
| --- | --- |
| `build` | `--all`, `--package <name>`, `--el <8\|9\|10>`, `--arch <x86_64\|aarch64>`, `--list`, `--check-sources`, `--dry-run`, `-h`, `--help` |
| `sign` | `--force`, `--rpm-types <binary\|source\|both>` (default: `both`), `--input-dir <dir>` (default: `runtime/artifacts`), `--output-dir <dir>` (default: sign in place), `--runtime <dir>` (default: `runtime`), `--dry-run`, `-h`, `--help` |
| `verify` | `--rpm-types <binary\|source\|both>` (default: `both`), `--input-dir <dir>` (default: `runtime/artifacts`), `--runtime <dir>` (default: `runtime`), `--public-key <file>` (default: first staged public key), `-h`, `--help` |
| `repo` | `--public-key <file>` (default: first staged public key), `--allow-unsigned` (local-only validation bypass), `--runtime <dir>` (default: `runtime`), optional positional arguments: `[INPUT_DIR] [OUTPUT_DIR]` where defaults are `runtime/artifacts` and `runtime/repo` |
| `prune` | `--root <path>` (default: `runtime/repo`), `--keep <N>` (default: `3`), `--dry-run`, `-h`, `--help` |

Examples:

```bash
./scripts/package-workflow.sh sign --rpm-types binary
./scripts/package-workflow.sh repo runtime/artifacts runtime/repo-test
./scripts/package-workflow.sh repo --allow-unsigned runtime/artifacts runtime/repo-test
./scripts/package-workflow.sh prune --root runtime/repo --keep 3
```

The package commands use Docker Compose internally. See [build-and-stage.md](build-and-stage.md), [signing.md](signing.md), and [publishing.md](publishing.md) for stage details and troubleshooting.
