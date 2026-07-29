#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

"""Regenerate CHANGELOG.md from git history using the rules in cliff.toml."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "cliff.toml"


def build_command(argv: list[str]) -> list[str]:
    """Build the git-cliff command for the given passthrough arguments.

    Args:
        argv: Arguments forwarded verbatim to git-cliff.

    Returns:
        The command as an argument list.
    """
    executable = Path(sys.executable).parent / "git-cliff"
    return [str(executable), "--config", str(CONFIG), *argv]


def main() -> int:
    """Run git-cliff and return its exit status."""
    return subprocess.run(build_command(sys.argv[1:]), check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
