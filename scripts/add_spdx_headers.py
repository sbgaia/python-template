#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

"""Insert SPDX licensing headers into Python files that lack them."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

COPYRIGHT_HOLDER = "the Python Template contributors"
LICENSE_ID = "BSD-2-Clause"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files to annotate. Supplied by pre-commit.",
    )
    parser.add_argument(
        "--year",
        default=str(date.today().year),
        help="Copyright year to write. Defaults to the current year.",
    )
    parser.add_argument(
        "--copyright",
        default=COPYRIGHT_HOLDER,
        dest="copyright_holder",
        help="Copyright holder to write into the header.",
    )
    parser.add_argument(
        "--license",
        default=LICENSE_ID,
        dest="license_id",
        help="SPDX license identifier to write into the header.",
    )
    return parser.parse_args()


def annotatable(paths: list[str]) -> list[str]:
    """Return the paths reuse can annotate.

    Zero-byte files are skipped because ``reuse lint`` ignores them, so
    annotating them would add content to intentionally empty files without
    improving compliance.

    Args:
        paths: Candidate file paths.

    Returns:
        The subset of paths that are non-empty regular files.
    """
    keep = []
    for raw in paths:
        path = Path(raw)
        if path.is_file() and path.stat().st_size > 0:
            keep.append(raw)
    return keep


def build_command(
    paths: list[str],
    *,
    year: str,
    copyright_holder: str,
    license_id: str,
) -> list[str]:
    """Build the ``reuse annotate`` command for the given paths.

    Args:
        paths: Files to annotate.
        year: Copyright year to write.
        copyright_holder: Copyright holder to write.
        license_id: SPDX license identifier to write.

    Returns:
        The command as an argument list.
    """
    return [
        sys.executable,
        "-m",
        "reuse",
        "annotate",
        "--skip-existing",
        "--merge-copyrights",
        "--skip-unrecognised",
        "--year",
        year,
        "--copyright",
        copyright_holder,
        "--license",
        license_id,
        *paths,
    ]


def main() -> int:
    """Annotate the requested files and return the reuse exit status."""
    args = parse_args()
    paths = annotatable(args.paths)
    if not paths:
        return 0

    command = build_command(
        paths,
        year=args.year,
        copyright_holder=args.copyright_holder,
        license_id=args.license_id,
    )
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
