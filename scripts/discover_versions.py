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
GITHUB_RELEASES_API = "https://api.github.com/repos/{repo}/releases"


def load_upstreams(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    with path.open("r") as f:
        return yaml.safe_load(f)


def fetch_github_latest_release(repo: str) -> dict:
    url = GITHUB_LATEST_RELEASE_API.format(repo=repo)
    headers = github_headers()

    resp = requests.get(url, timeout=15, headers=headers)
    resp.raise_for_status()
    return resp.json()


def github_headers() -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "prometheus-rpm-discover-versions",
    }
    github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    return headers


def fetch_github_releases(repo: str) -> list[dict]:
    url = GITHUB_RELEASES_API.format(repo=repo)
    headers = github_headers()
    releases: list[dict] = []

    page = 1
    while True:
        resp = requests.get(
            url,
            timeout=15,
            headers=headers,
            params={"per_page": 100, "page": page},
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        releases.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    return releases


def normalise_tag(tag: str | None) -> str:
    if not tag:
        return ""
    return re.sub(r"^v(?=\d)", "", tag)


def version_components(value: str | None) -> tuple[int, ...] | None:
    normalised = normalise_tag(value)
    if not normalised:
        return None
    parts = normalised.split(".")
    if not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def release_line_components(series: str | None) -> tuple[int, ...] | None:
    if series is None:
        return None

    raw = str(series).strip()
    if raw.startswith("v"):
        raise RuntimeError("releases.series must not include a leading v; use a quoted value such as 3.5")

    if not re.fullmatch(r"\d+\.\d+", raw):
        raise RuntimeError("releases.series must be a quoted dotted release line such as 3.5")

    components = tuple(int(part) for part in raw.split("."))
    if not components or len(components) < 2:
        raise RuntimeError("releases.series must be a dotted release line such as 3.5")
    return components


def release_matches_constraints(release: dict, releases_cfg: dict) -> bool:
    if release.get("draft") or release.get("prerelease"):
        return False

    tag = release.get("tag_name") or ""

    tag_regex = releases_cfg.get("tag_regex")
    if tag_regex and not re.search(tag_regex, tag):
        return False

    series = releases_cfg.get("series")
    if series:
        expected_line = release_line_components(str(series))
        tag_components = version_components(tag)
        if not tag_components or tag_components[: len(expected_line)] != expected_line:
            return False

    return True


def fetch_github_selected_release(repo: str, releases_cfg: dict) -> dict:
    releases = fetch_github_releases(repo)
    for release in releases:
        if release_matches_constraints(release, releases_cfg):
            return release
    raise RuntimeError("no matching release found")


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
            if releases.get("series") or releases.get("tag_regex"):
                release = fetch_github_selected_release(repo, releases)
            else:
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
