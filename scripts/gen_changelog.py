#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

"""Regenerate CHANGELOG.md from git history using the rules in cliff.toml."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "cliff.toml"


def git_cliff_executable() -> str:
    """Locate the git-cliff binary.

    git-cliff ships as a dev dependency, so it normally sits next to the
    running interpreter. The PATH is searched as a fallback for the case
    where this script is run with an interpreter from outside that
    environment.

    Returns:
        The path to the git-cliff binary.

    Raises:
        SystemExit: If no git-cliff binary can be found.
    """
    candidate = Path(sys.executable).parent / "git-cliff"
    for path in (candidate, candidate.with_suffix(".exe")):
        if path.exists():
            return str(path)

    found = shutil.which("git-cliff")
    if found is None:
        raise SystemExit(
            "error: git-cliff not found; install the dev extra with "
            "'uv sync --extra dev'"
        )
    return found


def build_command(argv: list[str]) -> list[str]:
    """Build the git-cliff command for the given passthrough arguments.

    Args:
        argv: Arguments forwarded verbatim to git-cliff.

    Returns:
        The command as an argument list.
    """
    return [git_cliff_executable(), "--config", str(CONFIG), *argv]


def main() -> int:
    """Run git-cliff and return its exit status."""
    return subprocess.run(build_command(sys.argv[1:]), check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
