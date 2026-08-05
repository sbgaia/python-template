#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

"""Update the README coverage block from coverage.py XML output."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

COVERAGE_START = "<!-- coverage:start -->"
COVERAGE_END = "<!-- coverage:end -->"


@dataclass(frozen=True)
class CoverageResult:
    """Coverage totals extracted from coverage.py XML."""

    percent: float
    lines_valid: int
    lines_covered: int
    branches_valid: int
    branches_covered: int


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--coverage-xml",
        default="coverage.xml",
        type=Path,
        help="coverage.py XML report to read.",
    )
    parser.add_argument(
        "--readme",
        default="README.md",
        type=Path,
        help="README file to update.",
    )
    parser.add_argument(
        "--pyproject",
        default="pyproject.toml",
        type=Path,
        help="pyproject.toml file containing the coverage threshold.",
    )
    return parser.parse_args()


def read_coverage(path: Path) -> CoverageResult:
    """Read aggregate coverage values from coverage.py XML."""
    root = ElementTree.parse(path).getroot()
    line_rate = float(root.attrib["line-rate"])
    return CoverageResult(
        percent=line_rate * 100,
        lines_valid=int(root.attrib["lines-valid"]),
        lines_covered=int(root.attrib["lines-covered"]),
        branches_valid=int(root.attrib.get("branches-valid", "0")),
        branches_covered=int(root.attrib.get("branches-covered", "0")),
    )


def read_threshold(path: Path) -> float:
    """Read the configured coverage threshold from pyproject.toml."""
    content = path.read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^\[tool\.coverage\.report\].*?^fail_under\s*=\s*([0-9.]+)",
        content,
    )
    if match is None:
        return 0.0
    return float(match.group(1))


def badge_color(percent: float) -> str:
    """Return a Shields.io badge color for the coverage percentage."""
    if percent >= 90:
        return "brightgreen"
    if percent >= 80:
        return "green"
    if percent >= 70:
        return "yellow"
    if percent >= 60:
        return "orange"
    return "red"


def badge_percent(percent: float) -> str:
    """Format coverage for a Shields.io badge URL."""
    value = f"{percent:.2f}".rstrip("0").rstrip(".")
    return f"{value}%25"


def render_coverage_block(result: CoverageResult, threshold: float) -> str:
    """Render the README coverage block."""
    color = badge_color(result.percent)
    badge = (
        "![Coverage]"
        f"(https://img.shields.io/badge/coverage-"
        f"{badge_percent(result.percent)}-{color})"
    )
    return (
        f"{COVERAGE_START}\n\n"
        f"{badge}\n\n"
        f"Current coverage: **{result.percent:.2f}%**. "
        f"Required minimum: **{threshold:.2f}%**.\n\n"
        "Coverage details: "
        f"{result.lines_covered}/{result.lines_valid} statements and "
        f"{result.branches_covered}/{result.branches_valid} branches covered.\n"
        "CI updates this block from `coverage.xml` after the coverage "
        "workflow runs.\n\n"
        f"{COVERAGE_END}"
    )


def update_readme(path: Path, coverage_block: str) -> None:
    """Replace the README coverage block in place."""
    content = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(COVERAGE_START)}.*?{re.escape(COVERAGE_END)}",
        re.DOTALL,
    )
    if not pattern.search(content):
        raise ValueError(
            f"{path} does not contain {COVERAGE_START!r} and "
            f"{COVERAGE_END!r} markers."
        )
    updated = pattern.sub(coverage_block, content, count=1)
    if updated != content:
        path.write_text(updated, encoding="utf-8")


def main() -> int:
    """Update README coverage from the configured report files."""
    args = parse_args()
    result = read_coverage(args.coverage_xml)
    threshold = read_threshold(args.pyproject)
    update_readme(args.readme, render_coverage_block(result, threshold))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
