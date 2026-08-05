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
OUTPUT_FLAGS = ("-o", "--output", "-p", "--prepend")


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


def output_path(argv: list[str]) -> Path | None:
    """Return the changelog file git-cliff writes, if any.

    Args:
        argv: Arguments forwarded to git-cliff.

    Returns:
        The path written by ``-o``/``--output`` or ``-p``/``--prepend``, or
        None when git-cliff writes to stdout.
    """
    for index, arg in enumerate(argv):
        for flag in OUTPUT_FLAGS:
            if arg == flag and index + 1 < len(argv):
                return Path(argv[index + 1])
            if arg.startswith(f"{flag}="):
                return Path(arg.split("=", 1)[1])
    return None


def normalize(path: Path) -> None:
    """Strip whitespace the pre-commit hooks would otherwise strip.

    git-cliff appends a newline of its own after the rendered body, which
    leaves the blank line that separates two releases stranded at the end of
    the file. The trailing-whitespace and end-of-file-fixer hooks both undo
    that, so a release would fail its first hook pass on a file it had just
    generated. Normalising here keeps the generated changelog identical to
    the committed one.

    Args:
        path: The changelog file to normalize in place.
    """
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    lines = [line.rstrip() for line in text.split("\n")]
    normalized = "\n".join(lines).rstrip("\n") + "\n"
    if normalized != text:
        path.write_text(normalized, encoding="utf-8")


def main() -> int:
    """Run git-cliff, normalize its output, and return its exit status."""
    argv = sys.argv[1:]
    status = subprocess.run(build_command(argv), check=False).returncode
    path = output_path(argv)
    if status == 0 and path is not None:
        normalize(path)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
