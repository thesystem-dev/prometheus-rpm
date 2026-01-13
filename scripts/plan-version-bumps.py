#!/usr/bin/env python3
"""
Compare spec versions with latest upstream releases and print bump commands.

Relies on scripts/discover_versions.py to fetch upstream metadata.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DISCOVER = ROOT / "scripts" / "discover_versions.py"
UPSTREAMS = ROOT / "upstreams.yaml"
SPECS_DIR = ROOT / "specs"


def run_discover(cache: Path | None) -> dict:
    if cache:
        with cache.open("r") as fh:
            return yaml.safe_load(fh)

    proc = subprocess.run(
        [sys.executable, str(DISCOVER)],
        check=True,
        capture_output=True,
        text=True,
    )
    return yaml.safe_load(proc.stdout)


def parse_spec(path: Path) -> tuple[str, str]:
    name = None
    version = None

    with path.open("r") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped.startswith("Name:"):
                name = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("Version:"):
                version = stripped.split(":", 1)[1].strip()
            if name and version:
                break

    if not name or not version:
        raise RuntimeError(f"Failed to parse Name/Version from {path}")

    return name, version


def extract_latest(entry: dict) -> str | None:
    assets = entry.get("assets") or []
    versions = {asset.get("version") for asset in assets if asset.get("version")}

    if len(versions) == 1:
        return versions.pop()
    if len(versions) > 1:
        raise RuntimeError(f"Ambiguous asset versions: {versions}")

    return entry.get("tag")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan rpmdev-bumpspec commands for outdated specs."
    )
    parser.add_argument(
        "--discover-cache",
        type=Path,
        help="Use YAML output from discover_versions.py instead of hitting GitHub.",
    )
    parser.add_argument(
        "--write-script",
        type=Path,
        help="Optional path to write a shell script with bump commands.",
    )
    args = parser.parse_args()

    try:
        upstream = run_discover(args.discover_cache)
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: discover_versions.py failed: {exc.stderr}", file=sys.stderr)
        return 1

    commands: list[str] = []
    outdated: list[str] = []

    for spec_path in sorted(SPECS_DIR.glob("*.spec")):
        spec_name = spec_path.stem
        name, current = parse_spec(spec_path)
        entry = upstream.get(spec_name) or upstream.get(name)
        if not entry:
            print(f"[WARN] No upstream data for {spec_name}", file=sys.stderr)
            continue

        latest = extract_latest(entry)
        # Normalise common tag style like 'v1.2.3' to RPM-friendly '1.2.3'
        if latest:
            latest = re.sub(r'^v(?=\d)', '', latest)
        if not latest or latest == current:
            continue

        comment = f'Rebase to upstream version {latest}'
        cmd = (
            f'rpmdev-bumpspec --comment "{comment}" '
            f"-n {latest} specs/{spec_path.name}"
        )
        outdated.append(f"{spec_name}: {current} -> {latest}")
        commands.append(cmd)

    if not commands:
        print("All specs already match upstream versions.")
        return 0

    print("Specs needing bumps:")
    for line in outdated:
        print(f"  - {line}")

    print("\nSuggested commands:")
    for cmd in commands:
        print(f"  {cmd}")

    if args.write_script:
        args.write_script.write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\n"
            + "\n".join(commands)
            + "\n"
        )
        args.write_script.chmod(0o755)
        print(f"\nWrote helper script to {args.write_script}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
