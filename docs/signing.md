# RPM Signing

This document describes how to sign RPMs in this repository using the Docker builder image and `scripts/sign-rpms.sh`.

## Overview

RPM signing cryptographically signs packages using GPG (GNU Privacy Guard). Signed RPMs provide:

- **Package integrity** – verify packages haven't been tampered with.
- **Source authentication** – confirm packages come from the expected publisher.
- **Trust chain** – allow users to establish trust through GPG key verification.

RPM signatures are embedded in the package header and verified during installation with `rpm --checksig` or automatically by DNF when the public key is imported into the RPM database.

## 1. Requirements

- Run all commands from the repository root.
- Run `./scripts/stage-runtime.sh --key-id <GPG_KEY> --packager '<Name <email>>'` before exporting keys so the `runtime/` tree exists.
- A usable GPG key pair for signing (see `gpg --list-secret-keys`).
- Docker with Compose; always pass `-f docker/docker-compose.yml`.

### GPG Key

You need a GPG key pair for signing. If you don't have one:

**Generate a new key:**

```bash
gpg --full-generate-key
```

- Choose RSA and RSA (default)
- Recommended key size: 4096 bits
- Set appropriate expiration (e.g., 1–2 years)
- Use a strong passphrase

**Or use an existing key:**

```bash
gpg --list-secret-keys --keyid-format LONG
```

For more details on GPG key management, see the [GNU Privacy Handbook](https://www.gnupg.org/gph/en/manual/c14.html).

## 2. Export Key Material

After staging the runtime tree, export your key into `runtime/gnupg/`:

```bash
KEY_ID="<YOUR_KEY_ID>"

# Private key (required)
gpg --export-secret-keys "$KEY_ID" > runtime/gnupg/private.asc
chmod 600 runtime/gnupg/private.asc

# Public key (required for verification; ASCII-armoured)
gpg --armor --export "$KEY_ID" > runtime/gnupg/RPM-GPG-KEY-thesystem-dev

# Ownertrust (optional; only if you have trust assignments to retain)
gpg --export-ownertrust > runtime/gnupg/ownertrust.txt
```

## 3. Sign RPMs

### Interactive mode

```bash
docker compose -f docker/docker-compose.yml run --rm sign
```
- Prompts for the passphrase via pinentry.
- Signs every unsigned RPM/SRPM inside `runtime/artifacts/`.

### Non-interactive mode (CI or headless systems)

```bash
export GPG_PASSPHRASE='your-passphrase'
docker compose -f docker/docker-compose.yml run --rm -e GPG_PASSPHRASE sign
```
- Runs `rpmsign --addsign` non-interactively via an Expect script (passphrase provided by `GPG_PASSPHRASE`).
- Add `--force` to re-sign even if signatures already exist (see below).

Logs are written to `runtime/artifacts/signing.log` for later review.

### Signing output

During signing operations, the script prints per-RPM status lines:

```
SUCCESS: prometheus-2.45.0-1.el9.x86_64.rpm
SKIP:    node_exporter-1.6.1-1.el9.x86_64.rpm (already signed)
FAIL:    alertmanager-0.25.0-1.el9.x86_64.rpm
```

A summary with counts is printed after processing completes.

### Default behaviour

When run without flags, the helper:
- Scans `runtime/artifacts/el*/` for `.rpm` and `.src.rpm`.
- Signs only the files lacking signatures (skips the rest).
- Modifies RPMs in place (no copies).
- Records progress in `runtime/artifacts/signing.log`.

### Force re-signing

Re-sign all RPMs, including those already signed:

```bash
docker compose -f docker/docker-compose.yml run --rm -e GPG_PASSPHRASE sign --force
```

**Use cases:**
- Key rotation (replacing old signatures with a new key)
- Repairing signature corruption
- Switching signature algorithms or digest settings

### Dry-run mode

Preview what would be signed without modifying files:

```bash
docker compose -f docker/docker-compose.yml run --rm sign --dry-run
```

Example output:

```
[WOULD SIGN]    prometheus-2.45.0-1.el9.x86_64.rpm
[WOULD SKIP]    node_exporter-1.6.1-1.el9.x86_64.rpm (already signed)
[WOULD RE-SIGN] alertmanager-0.25.0-1.el9.x86_64.rpm

Summary: 2 would be signed, 1 would be skipped
```

Combine with `--force` to see which RPMs would be re-signed.

### Filter by RPM type

Limit signing to binary or source RPMs:

```bash
# Binary RPMs only (excludes .src.rpm)
docker compose -f docker/docker-compose.yml run --rm sign --rpm-types binary

# Source RPMs only
docker compose -f docker/docker-compose.yml run --rm sign --rpm-types source

# Both (default)
docker compose -f docker/docker-compose.yml run --rm sign --rpm-types both
```

### Output directory (non-destructive)

Copy signed RPMs to a parallel tree instead of modifying originals:

```bash
docker compose -f docker/docker-compose.yml run --rm sign --output-dir runtime/signed
```

- Preserves the original `runtime/artifacts/` contents.
- Creates `runtime/signed/el*/<arch>/` directories mirroring the source layout.

### Custom input directory

Sign RPMs from an alternate path:

```bash
docker compose -f docker/docker-compose.yml run --rm sign --input-dir /path/to/rpms
```

Combine with dry-run to preview actions against a custom location:

```bash
docker compose -f docker/docker-compose.yml run --rm sign --dry-run --input-dir /tmp/test-rpms
```

## 4. Verify Signatures

1. **Audit entire tree**
   ```bash
   docker compose -f docker/docker-compose.yml run --rm sign --verify
   ```
   The script imports `runtime/gnupg/RPM-GPG-KEY-thesystem-dev` into a temporary RPM database and prints `[OK] SIGNED`, `[?] SIGNED*`, or `[!!] UNSIGNED` per file:
   ```
   [OK] SIGNED:      prometheus-2.45.0-1.el9.x86_64.rpm
   [?] SIGNED*:      node_exporter-1.6.1-1.el9.x86_64.rpm (missing public key)
   [!!] UNSIGNED:    alertmanager-0.25.0-1.el9.x86_64.rpm

   Summary: 1 signed, 1 signed (missing key), 1 unsigned
   ```
   `SIGNED*` indicates the public key was not available when verification ran; confirm the armoured key exists in `runtime/gnupg/`.

2. **Inspect a single RPM**
   ```bash
   docker compose -f docker/docker-compose.yml run --rm builder -- \
     rpm -Kv runtime/artifacts/<el>/<arch>/<package>.rpm
   ```
   Signed packages show `Signature, key ID ...: OK`; unsigned ones show `Signature: (none)`.

### Troubleshooting

- **`SIGNED*` output:** Ensure `runtime/gnupg/RPM-GPG-KEY-thesystem-dev` (ASCII-armoured) exists; rerun `sign --verify`.
- **`ERROR: GPG_PASSPHRASE not set and no TTY available`:** set `GPG_PASSPHRASE` before invoking the container.
- **Unexpected failures:** inspect `runtime/artifacts/signing.log` for per-RPM details.

## 5. Publish (create repository metadata)

```bash
docker compose -f docker/docker-compose.yml run --rm builder \
  ./scripts/create-repo.sh
```

This copies RPMs into `runtime/repo/` and runs `createrepo_c`, preserving the signatures for downstream consumers.

See [docs/publishing.md](publishing.md) for instructions on syncing `runtime/repo/` and exposing the repository to users.
