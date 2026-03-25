#!/usr/bin/env python3
"""
Synchronize source SHA256 values in upstreams.yaml and matching RPM specs.

Workflow:
- prefer GitHub release asset digests when available
- fall back to locally computed SHA256 when no upstream digest is present
- update only packages that already declare releases.checksums in upstreams.yaml
  and use %global *_sha macros in their specs
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
DISCOVER = ROOT / "scripts" / "discover_versions.py"
UPSTREAMS = ROOT / "upstreams.yaml"
SPECS_DIR = ROOT / "specs"

SHA_LINE_RE = re.compile(
    r"^(?P<prefix>\s*%global\s+)(?P<name>\S+_sha)(?P<gap>\s+)"
    r"(?P<value>[0-9A-Fa-f]{64})(?P<suffix>\s*)$"
)


def run_discover() -> dict:
    proc = subprocess.run(
        [sys.executable, str(DISCOVER)],
        check=True,
        capture_output=True,
        text=True,
    )
    return yaml.safe_load(proc.stdout)


def load_upstreams() -> dict:
    with UPSTREAMS.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def save_upstreams(data: dict) -> None:
    with UPSTREAMS.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False)


def normalise_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def asset_to_checksum_key(asset_name: str, checksum_keys: list[str]) -> str | None:
    if asset_name in checksum_keys:
        return asset_name

    asset_token = normalise_token(asset_name)
    matches: list[tuple[int, str]] = []
    for key in checksum_keys:
        key_token = normalise_token(key)
        if key_token and key_token in asset_token:
            matches.append((len(key_token), key))

    if matches:
        matches.sort(reverse=True)
        if len(matches) > 1 and matches[0][0] == matches[1][0]:
            raise RuntimeError(
                f"ambiguous checksum key mapping for asset {asset_name}: "
                f"{matches[0][1]} vs {matches[1][1]}"
            )
        return matches[0][1]

    if len(checksum_keys) == 1:
        return checksum_keys[0]

    return None


def digest_to_sha256(digest: str | None) -> str | None:
    if not digest:
        return None
    if not digest.startswith("sha256:"):
        return None
    value = digest.split(":", 1)[1].strip().lower()
    if re.fullmatch(r"[0-9a-f]{64}", value):
        return value
    return None


def sha256_from_url(url: str) -> str:
    h = hashlib.sha256()
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if chunk:
                h.update(chunk)
    return h.hexdigest()


def checksum_source(asset: dict) -> tuple[str, str]:
    sha = digest_to_sha256(asset.get("digest"))
    if sha:
        return sha, "github-digest"

    url = asset.get("url")
    if not url:
        raise RuntimeError(f"asset has no download URL: {asset.get('name')}")
    return sha256_from_url(url), "local-sha256"


def spec_sha_updates(checksums: dict[str, str]) -> tuple[str | None, str | None]:
    if not checksums:
        return None, None

    arm_key = None
    for key in checksums:
        token = normalise_token(key)
        if "arm64" in token or token.endswith("arm"):
            arm_key = key
            break

    amd_key = None
    for key in checksums:
        if key == arm_key:
            continue
        amd_key = key
        break

    if arm_key and amd_key:
        return checksums[arm_key], checksums[amd_key]
    if arm_key:
        return checksums[arm_key], None
    if amd_key:
        return None, checksums[amd_key]

    # Single non-arm checksum entry: treat as the default branch.
    only_value = next(iter(checksums.values()))
    return None, only_value


def update_spec_sha_macros(spec_path: Path, checksums: dict[str, str]) -> bool:
    lines = spec_path.read_text(encoding="utf-8").splitlines()
    arm_sha, amd_sha = spec_sha_updates(checksums)
    changed = False

    ifarch_stack: list[str] = []
    current_branch = "global"
    sha_lines_seen = 0
    targetable_sha_lines = 0

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("%ifarch "):
            target = stripped.split(None, 1)[1]
            ifarch_stack.append(current_branch)
            if target == "aarch64":
                current_branch = "aarch64"
            else:
                current_branch = f"unsupported-ifarch:{target}"
            continue
        if stripped == "%else":
            if current_branch == "aarch64":
                current_branch = "else-after-aarch64"
            elif current_branch.startswith("unsupported-ifarch:"):
                current_branch = f"unsupported-else:{current_branch.split(':', 1)[1]}"
            continue
        if stripped == "%endif":
            current_branch = ifarch_stack.pop() if ifarch_stack else "global"
            continue

        match = SHA_LINE_RE.match(line)
        if not match:
            continue

        sha_lines_seen += 1

        replacement = None
        if current_branch == "aarch64" and arm_sha:
            replacement = arm_sha
        elif current_branch in {"else-after-aarch64", "global"} and amd_sha:
            replacement = amd_sha
        elif current_branch == "global" and arm_sha and amd_sha is None:
            replacement = arm_sha
        elif current_branch.startswith("unsupported-"):
            raise RuntimeError(
                f"Unsupported %ifarch layout for SHA macro in {spec_path}: {current_branch}"
            )

        if replacement:
            targetable_sha_lines += 1

        if replacement and replacement != match.group("value"):
            lines[idx] = (
                f"{match.group('prefix')}{match.group('name')}"
                f"{match.group('gap')}{replacement}{match.group('suffix')}"
            )
            changed = True

    if sha_lines_seen == 0:
        return False
    if targetable_sha_lines == 0:
        raise RuntimeError(f"No targetable SHA macros found in {spec_path}")

    if changed:
        spec_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync upstream/source SHA256 values into metadata and specs."
    )
    parser.add_argument(
        "--package",
        action="append",
        default=[],
        help="Limit updates to a package/project name (repeatable).",
    )
    args = parser.parse_args()

    package_filter = set(args.package)
    try:
        discovery = run_discover()
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: discover_versions.py failed: {exc.stderr}", file=sys.stderr)
        return 1

    try:
        upstreams = load_upstreams()
        projects = upstreams.get("projects", {})

        updates = 0
        checked_packages = 0
        fallback_assets: list[str] = []

        for project_name, cfg in projects.items():
            rpm_name = cfg.get("packaging", {}).get("rpm_name", project_name)
            if package_filter and project_name not in package_filter and rpm_name not in package_filter:
                continue

            releases = cfg.get("releases", {})
            checksum_map = releases.get("checksums")
            if not checksum_map:
                continue

            checked_packages += 1

            spec_path = SPECS_DIR / f"{rpm_name}.spec"
            if not spec_path.exists():
                raise RuntimeError(
                    f"Missing spec for checksum-managed package: {spec_path.name}"
                )

            discovered = discovery.get(project_name) or discovery.get(rpm_name)
            if not discovered or discovered.get("error"):
                raise RuntimeError(f"No usable discovery data for {rpm_name}")

            assets = discovered.get("assets") or []
            checksum_keys = list(checksum_map.keys())
            updated_checksums = dict(checksum_map)
            project_changed = False

            for asset in assets:
                key = asset_to_checksum_key(asset.get("name", ""), checksum_keys)
                if not key:
                    continue
                sha, source = checksum_source(asset)
                if source == "local-sha256":
                    fallback_assets.append(f"{rpm_name}: {asset.get('name')}")
                if updated_checksums.get(key) != sha:
                    updated_checksums[key] = sha
                    project_changed = True

            if not project_changed:
                continue

            releases["checksums"] = updated_checksums

            update_spec_sha_macros(spec_path, updated_checksums)

            updates += 1
            print(f"Updated checksum metadata for {rpm_name}")

        if checked_packages == 0 and package_filter:
            raise RuntimeError("No checksum-managed packages matched the requested filter")

        if updates == 0:
            print("Checksum metadata already matches discovered assets.")
            return 0

        save_upstreams(upstreams)

        if fallback_assets:
            print("\nUsed locally computed SHA256 for assets without upstream digests:")
            for line in fallback_assets:
                print(f"  - {line}")

        return 0
    except Exception as exc:
        print(f"ERROR: checksum sync failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
