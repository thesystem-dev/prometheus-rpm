# Runtime Preparation

`scripts/stage-runtime.sh` provisions the transient `runtime/` tree used by the build/sign/publish workflow. It creates the on-disk directories, refreshes `runtime/rpmmacros` from `templates/rpmmacros`, and performs safety checks so mock, rpmsign, and other helpers see a consistent layout across macOS, LXC, and Docker environments.

## Directory Layout

Running the helper ensures the following structure exists (all paths are relative to the repository root):

```
runtime/
├── artifacts/        # mock results (binary RPMs, SRPMs, logs)
├── repo/             # createrepo_c output + staged repository metadata
├── SOURCES/          # spectool cache shared across builds
├── gnupg/            # drop exported signing keys/ownertrust here
└── rpmmacros         # rendered from templates/rpmmacros
```

`runtime/gnupg` is created with `0700` permissions so that imported keys remain private. `runtime/rpmmacros` is written with `0600` permissions so only the current user can read it.

## Running the Helper

Stage the runtime tree before running any build or signing scripts:

```bash
./scripts/stage-runtime.sh --key-id ABCDEF1234567890 \
  --packager "Your Name <you@example.com>"
```

- `--key-id` updates `%_gpg_name` in `runtime/rpmmacros` so rpmsign knows which key to use.
- `--packager` sets the `%packager` header for subsequent spec bumps/builds.
- Re-run the command with `--force` whenever you need to regenerate the macros file (for example, after editing `templates/rpmmacros`).

## Options

```
--runtime <dir>     Target runtime directory (default: runtime)
--templates <dir>   Source template directory (default: templates)
--results <dir>     Results directory to create (default: runtime/artifacts)
--repo <dir>        Repository directory to create (default: runtime/repo)
--sources <dir>     Source directory for --check-sources (default: sources)
--check-sources     Only validate source basenames, do not stage runtime files
--key-id <id>       Override %_gpg_name in runtime/rpmmacros
--packager <str>    Override %packager in runtime/rpmmacros
--force             Overwrite runtime/rpmmacros even if it already exists
```

Most setups can rely on the defaults; the `--runtime/--results/--repo` flags are primarily for CI systems that need to redirect paths.

## Source Validation

The script refuses to run if two different packages ship files with the same basename (for example, both `sources/foo/service.service` and `sources/bar/service.service`). Use `--check-sources` to audit the tree:

```bash
./scripts/stage-runtime.sh --check-sources
```

Resolve any conflicts before staging the runtime directories so spec builds never pick up the wrong file.

## GPG Material

`stage-runtime.sh` does not copy your keys—it simply prepares `runtime/gnupg/`. Export the signing key and ownertrust yourself:

```bash
gpg --export-secret-keys ABCDEF1234567890 > runtime/gnupg/private.asc
gpg --export-ownertrust > runtime/gnupg/ownertrust.txt  # optional
```

The signing helper imports these files into an ephemeral `GNUPGHOME`, so never copy your entire `~/.gnupg` directory into the repo. Keep the exported key material armoured, add it to `.gitignore`, and treat the runtime tree as disposable state.
