# Version & Upstream Tracking

Upstream releases are tracked using a simple metadata model and helper scripts. The `upstreams.yaml` file defines each packaged exporter, including its upstream repository, release artefacts, expected checksums, and supported architectures.

## Helper Scripts

| Script | Purpose |
| --- | --- |
| `scripts/discover_versions.py` | Calls the upstream release API (GitHub for now) and prints the latest version plus the artefacts that match the regex in `upstreams.yaml`. |
| `scripts/plan-version-bumps.py` | Reads the discovery output, compares it with the `Version:` field in each spec, and prints the `rpmdev-bumpspec` commands needed to catch up. Use `--write-script` to emit a helper shell script. |
| `scripts/generate_exporter_inventory.py` | Builds `docs/exporters.md`, a table that summarises package names, upstream project URLs, licences, and supported architectures. |

All three scripts are **read-only** and rely exclusively on `upstreams.yaml`. They intentionally avoid modifying spec files, ensuring that changelog updates remain manual and auditable.

## Running the Helpers

On macOS, the system Python is built against LibreSSL, which can lead to compatibility differences. For consistency, the helper scripts should be run using the official slim Python container.

### GitHub API token (recommended)

`discover_versions.py` calls GitHub Releases APIs and can hit unauthenticated rate limits (`403 rate limit exceeded`) in busy periods.

Using a token is **recommended** but **not required**:

- Required only when unauthenticated limits are exceeded
- Optional for occasional/manual runs

Create a token in GitHub (fine-grained preferred):

1. Go to `https://github.com/settings/personal-access-tokens`
2. Create a **Fine-grained token** with:
   - **Token name:** `prometheus-rpm-upstream-discovery`
   - **Description:** `Used by discover_versions.py and plan-version-bumps.py to query GitHub release metadata`
   - **Repository access:** `Public repositories (read-only)`
   - **Expiration:** per your policy (for example, 90 days)
3. Export it in your shell:

```bash
export GITHUB_TOKEN="<token>"
```

`scripts/discover_versions.py` accepts either `GITHUB_TOKEN` or `GH_TOKEN`.
If you already use GitHub CLI auth, exporting `GH_TOKEN` is also supported.
If your environment does not allow fine-grained tokens for this workflow, use a classic PAT with `public_repo`.

```bash
docker run --rm -e GITHUB_TOKEN -e PIP_DISABLE_PIP_VERSION_CHECK=1 -v "$PWD":/work -w /work python:3.14-slim \
  bash -lc "pip install -r requirements.txt && python scripts/discover_versions.py"

docker run --rm -e GITHUB_TOKEN -e PIP_DISABLE_PIP_VERSION_CHECK=1 -v "$PWD":/work -w /work python:3.14-slim \
  bash -lc "pip install -r requirements.txt && python scripts/plan-version-bumps.py --write-script runtime/bump.sh"

docker run --rm -e GITHUB_TOKEN -e PIP_DISABLE_PIP_VERSION_CHECK=1 -v "$PWD":/work -w /work python:3.14-slim \
  bash -lc "pip install -r requirements.txt && python scripts/generate_exporter_inventory.py"
```

If you have a local Python environment, `pip install -r requirements.txt` and run the scripts directly instead.

## Apply version bumps (container-only)

After generating the helper script, apply the spec bumps using the builder image. This updates the Version: and appends changelog entries via rpmdev-bumpspec.

First ensure the image exists:

```bash
docker compose -f docker/docker-compose.yml build builder
```

Then run the bump script inside the image:

```bash
docker run --rm \
  -v "$PWD":/home/builder \
  -w /home/builder \
  prometheus-rpm-builder:1.0 \
  ./runtime/bump.sh

git diff  # review changes before committing
```

Notes:

- Do not use the docker compose builder service to run `bump.sh`. Its volume layout mounts specs read-only under /home/builder/rpmbuild/SPECS and does not provide /home/builder/specs, so the helper cannot modify spec files in place.
- After bumping versions, regenerate the exporter inventory:

```bash
docker run --rm -e GITHUB_TOKEN -e PIP_DISABLE_PIP_VERSION_CHECK=1 -v "$PWD":/work -w /work python:3.14-slim \
  bash -lc "pip install -r requirements.txt && python scripts/generate_exporter_inventory.py"
```

## Updating Upstream Metadata

The helper scripts revolve around `upstreams.yaml`. When upstream releases move, follow this order to keep the metadata and docs aligned:

1. Update `upstreams.yaml` whenever you add an exporter or change its release artefact naming/checksum scheme.
2. Run `scripts/discover_versions.py` to ensure the metadata still matches upstream.
3. Use `scripts/plan-version-bumps.py` to generate the bump commands for any outdated specs. Then apply the changes as described in 'Apply version bumps (container-only)' above.
4. Rebuild `docs/exporters.md` so downstream users can see the full catalogue.

Future tooling (build, sign, publish) will reuse the same metadata, so keeping it accurate prevents churn when additional scripts are introduced.
