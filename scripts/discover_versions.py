#!/usr/bin/env python3
"""
Discover latest upstream versions based on upstreams.yaml.

This script is intentionally:
- read-only
- side-effect free
- schema-driven

It is NOT responsible for:
- spec parsing
- RPM building
- CI logic
"""

import re
import sys
import os
from pathlib import Path

import requests
import yaml

UPSTREAMS_FILE = Path("upstreams.yaml")
GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/{repo}/releases/latest"


def load_upstreams(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    with path.open("r") as f:
        return yaml.safe_load(f)


def fetch_github_latest_release(repo: str) -> dict:
    url = GITHUB_LATEST_RELEASE_API.format(repo=repo)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "prometheus-rpm-discover-versions",
    }
    github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    resp = requests.get(url, timeout=15, headers=headers)
    resp.raise_for_status()
    return resp.json()


def main() -> int:
    try:
        upstreams = load_upstreams(UPSTREAMS_FILE)
    except Exception as exc:
        print(f"ERROR: failed to load upstreams.yaml: {exc}", file=sys.stderr)
        return 1

    projects = upstreams.get("projects", {})
    results = {}

    for project_name, cfg in projects.items():
        display_name = cfg.get("display_name", project_name)
        upstream = cfg.get("upstream", {})
        releases = cfg.get("releases", {})

        vcs = upstream.get("vcs")
        repo = upstream.get("repo")

        if vcs != "github":
            results[project_name] = {
                "display_name": display_name,
                "error": f"unsupported VCS: {vcs}",
            }
            continue

        asset_pattern_raw = releases.get("asset_pattern")
        if not asset_pattern_raw:
            results[project_name] = {
                "display_name": display_name,
                "error": "missing releases.asset_pattern",
            }
            continue

        asset_pattern = re.compile(asset_pattern_raw)

        try:
            release = fetch_github_latest_release(repo)
        except Exception as exc:
            results[project_name] = {
                "display_name": display_name,
                "error": f"failed to fetch release: {exc}",
            }
            continue

        tag = release.get("tag_name")
        assets = release.get("assets", [])

        matched_assets = []
        for asset in assets:
            name = asset.get("name")
            match = asset_pattern.match(name)
            if not match:
                continue

            matched_assets.append(
                {
                    "name": name,
                    "url": asset.get("browser_download_url"),
                    "version": match.groupdict().get("version", tag),
                }
            )

        results[project_name] = {
            "display_name": display_name,
            "tag": tag,
            "assets": matched_assets,
        }

    yaml.safe_dump(results, sys.stdout, sort_keys=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
