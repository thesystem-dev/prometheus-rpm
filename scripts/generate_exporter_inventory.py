#!/usr/bin/env python3
"""
Generate docs/exporters.md from upstreams.yaml.

Usage:
    python scripts/generate_exporter_inventory.py
"""
from __future__ import annotations

import pathlib
import sys
from typing import Dict, List

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
UPSTREAMS = ROOT / "upstreams.yaml"
SPECS_DIR = ROOT / "specs"
DOC = ROOT / "docs" / "exporters.md"


def load_upstreams() -> Dict[str, dict]:
    with UPSTREAMS.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data.get("projects", {})


def read_spec_license(rpm_name: str) -> str:
    spec_path = SPECS_DIR / f"{rpm_name}.spec"
    if not spec_path.exists():
        return "UNKNOWN"
    for line in spec_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("license"):
            _, _, value = line.partition(":")
            return value.strip() or "UNKNOWN"
    return "UNKNOWN"


def build_rows(projects: Dict[str, dict]) -> List[Dict[str, str]]:
    rows = []
    for name, meta in projects.items():
        packaging = meta.get("packaging", {})
        rpm_name = packaging.get("rpm_name", name)
        display_name = meta.get("display_name", rpm_name)
        upstream = meta.get("upstream", {})
        url = upstream.get("project_url")
        repo = upstream.get("repo")
        if not url and repo:
            url = f"https://github.com/{repo}"
        architectures = packaging.get("architectures", [])
        rows.append(
            {
                "rpm": rpm_name,
                "display": display_name,
                "url": url or "N/A",
                "license": read_spec_license(rpm_name),
                "architectures": ", ".join(architectures) if architectures else "N/A",
            }
        )
    rows.sort(key=lambda item: item["rpm"])
    return rows


def write_doc(rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Exporter Inventory",
        "",
        "Auto-generated from `upstreams.yaml` by "
        "`scripts/generate_exporter_inventory.py`. "
        "Run the script after adding or updating exporters.",
        "",
        "| RPM Name | Display Name | Upstream | License | Architectures |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        upstream_link = (
            f"[{row['url']}]({row['url']})" if row["url"].startswith("http") else row["url"]
        )
        lines.append(
            f"| `{row['rpm']}` | {row['display']} | {upstream_link} | "
            f"{row['license']} | {row['architectures']} |"
        )
    lines.append("")
    DOC.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    projects = load_upstreams()
    rows = build_rows(projects)
    write_doc(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
