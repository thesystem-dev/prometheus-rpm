# Publishing Signed RPM Repositories

This guide explains how to turn the signed RPMs under `runtime/artifacts/` into a consumable DNF repository and publish it to a remote host (for example, via `rsync` or `scp`). All commands assume you are in the repository root and that RPMs have already been built (see [docs/build-and-stage.md](build-and-stage.md)) and signed (see [docs/signing.md](signing.md)).

## 1. Generate repository metadata

Run the helper inside the builder container so `createrepo_c` is available:

```bash
docker compose -f docker/docker-compose.yml run --rm builder \
  ./scripts/create-repo.sh
```

This copies all signed RPMs/SRPMs into `runtime/repo/el<EL>/<arch>/` and runs `createrepo_c --update` for each architecture. Expect to see directories such as:

```
runtime/repo/
└── el9/
    ├── x86_64/
    │   ├── repodata/
    │   └── *.rpm
    └── SRPMS/
        ├── repodata/
        └── *.src.rpm
```

## 2. Inspect the output

Before publishing, review the repo tree:

- Ensure each `repodata/` directory contains `repomd.xml`.
- Spot-check a few RPMs to confirm signatures remain intact:
  ```bash
  rpm -Kv runtime/repo/el9/x86_64/*.rpm | head -n 8
  ```

## 3. Copy the repository to your host

Use `rsync` (recommended) or `scp` to copy the entire `runtime/repo/` tree to the server that will host the repository:

```bash
rsync -av --delete runtime/repo/ user@host:/var/www/repos/prometheus-rpm/
```

Adjust the destination path to match your web server or file-share layout. The `--delete` flag keeps the remote tree in sync with your local content; drop it if you prefer manual cleanup.

## 4. Publish the GPG public key

Export the ASCII-armoured signing key (if you have not already) and upload it alongside the repo:

```bash
gpg --armor --export "$KEY_ID" > runtime/gnupg/RPM-GPG-KEY-thesystem-dev
scp runtime/gnupg/RPM-GPG-KEY-thesystem-dev user@host:/var/www/repos/prometheus-rpm/
```

Expose this key via HTTPS so consumers can import it before enabling the repo.

## 5. Serve the repository

Configure your HTTP server (nginx, Apache, etc.) to serve the published directory, for example:

```
https://packages.example.com/repos/prometheus-rpm/el9/x86_64/
```

Verify that `repodata/repomd.xml` is accessible via the browser or `curl`.

## 6. Consumer configuration

Direct users to [`docs/quickstart.md`](quickstart.md) for instructions on importing the key and adding the repository.

## 7. Future automation

The current workflow relies on manual `rsync`/`scp`. When you are ready to automate publishing (for example, via CI or Cloudflare R2), hook into the same `runtime/repo/` output and reuse the steps above.
