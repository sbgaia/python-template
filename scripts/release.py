#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

"""Prepare a release: bump the version, changelog, commit, and tag.

The release workflow at ``.github/workflows/release.yaml`` picks up the
pushed tag and publishes a GitHub Release with the matching CHANGELOG
section.

Usage:
    scripts/release.py X.Y.Z             # bump + commit + tag (no push)
    scripts/release.py X.Y.Z --push      # also push branch and tag
    scripts/release.py X.Y.Z --dry-run   # show what would happen
    scripts/release.py X.Y.Z --no-tag    # commit only, skip the tag
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[.-][0-9A-Za-z.-]+)?$")
VERSION_LINE = re.compile(r'^version\s*=\s*"[^"]*"', re.MULTILINE)

Runner = Callable[..., subprocess.CompletedProcess[str]]


def run(
    command: list[str],
    *,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a command, optionally capturing its output.

    Args:
        command: The command and its arguments.
        check: Raise on a non-zero exit status.
        capture: Capture stdout and stderr as text.

    Returns:
        The completed process.
    """
    return subprocess.run(
        command,
        check=check,
        capture_output=capture,
        text=True,
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("version", help="Release version, as X.Y.Z.")
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push the release commit and tag to origin.",
    )
    parser.add_argument(
        "--no-tag",
        action="store_true",
        help="Create the release commit without an annotated tag.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned steps without modifying anything.",
    )
    return parser.parse_args()


def validate_version(version: str) -> str:
    """Validate a release version string.

    Args:
        version: Candidate version.

    Returns:
        The version unchanged.

    Raises:
        ValueError: If the version is not of the form X.Y.Z.
    """
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(
            f"'{version}' is not a valid version (expected X.Y.Z)."
        )
    return version


def tag_exists(tag: str, *, runner: Runner = run) -> bool:
    """Return whether a git tag already exists.

    Args:
        tag: Tag name to look for.
        runner: Command runner, injectable for tests.

    Returns:
        True if the tag resolves.
    """
    result = runner(
        ["git", "rev-parse", "--verify", f"refs/tags/{tag}"],
        check=False,
        capture=True,
    )
    return result.returncode == 0


def working_tree_dirty(*, runner: Runner = run) -> bool:
    """Return whether the working tree has uncommitted changes.

    Args:
        runner: Command runner, injectable for tests.

    Returns:
        True if tracked files differ from HEAD.
    """
    result = runner(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        capture=True,
    )
    return bool(result.stdout.strip())


def previous_tag(*, runner: Runner = run) -> str | None:
    """Return the most recent version tag reachable from HEAD.

    Tags on unrelated branches are skipped automatically.

    Args:
        runner: Command runner, injectable for tests.

    Returns:
        The tag name, or None when no version tag is reachable.
    """
    result = runner(
        [
            "git",
            "describe",
            "--tags",
            "--abbrev=0",
            "--match=v[0-9]*",
            "HEAD",
        ],
        check=False,
        capture=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def changelog_range(prev: str | None) -> list[str]:
    """Return the git-cliff commit range arguments.

    Args:
        prev: The previous release tag, if any.

    Returns:
        A single-element range list, or an empty list for full history.
    """
    if prev is None:
        return []
    return [f"{prev}..HEAD"]


def bump_pyproject(path: Path, version: str) -> None:
    """Rewrite the project version in pyproject.toml.

    Args:
        path: Path to pyproject.toml.
        version: New version string.

    Raises:
        ValueError: If no version line is present.
    """
    content = path.read_text(encoding="utf-8")
    updated, count = VERSION_LINE.subn(
        f'version = "{version}"',
        content,
        count=1,
    )
    if count == 0:
        raise ValueError(f"No version line found in {path}.")
    path.write_text(updated, encoding="utf-8")


def sync_lockfile(*, runner: Runner = run) -> None:
    """Refresh uv.lock for the new version and verify it is in sync.

    uv.lock pins the project's own version, and CI runs with ``--locked``,
    so the lockfile must be regenerated alongside pyproject.toml.

    Args:
        runner: Command runner, injectable for tests.
    """
    runner(["uv", "lock"])
    runner(["uv", "lock", "--check"])


def generate_changelog(
    tag: str,
    prev: str | None,
    *,
    runner: Runner = run,
) -> None:
    """Write the new release section into CHANGELOG.md.

    With no previous tag the file is regenerated with ``-o``, because
    git-cliff refuses ``--prepend`` unless a range, ``-u``, or ``-l`` is
    given, and because only a full render emits the ``# Changelog``
    header. Once one release exists the file starts with that header
    followed by a blank line, which git-cliff recognises, so later
    releases are prepended above the previous section.

    Args:
        tag: The release tag, including the leading 'v'.
        prev: The previous release tag, if any.
        runner: Command runner, injectable for tests.
    """
    script = str(REPO_ROOT / "scripts" / "gen_changelog.py")
    if prev is None:
        runner([sys.executable, script, "--tag", tag, "-o", "CHANGELOG.md"])
        return
    runner(
        [
            sys.executable,
            script,
            "--tag",
            tag,
            *changelog_range(prev),
            "--prepend",
            "CHANGELOG.md",
        ]
    )


def run_hooks(files: list[str], *, runner: Runner = run) -> None:
    """Run the pre-commit hooks over the release files.

    The first pass may rewrite files (formatters, end-of-file-fixer), which
    pre-commit reports as a non-zero exit even though nothing is wrong, so
    its status is ignored. The second pass must come back clean.

    Args:
        files: Paths to check, passed to ``pre-commit run --files``.
        runner: Command runner, injectable for tests.
    """
    command = ["uv", "run", "pre-commit", "run", "--files", *files]
    runner(command, check=False)
    runner(command)


def main() -> int:
    """Run the release preparation process."""
    args = parse_args()
    # git, git-cliff, and uv all resolve paths against the current
    # directory. Anchoring to the repository root keeps a release invoked
    # from a subdirectory from writing the changelog somewhere else and
    # then aborting with the version bump already applied.
    os.chdir(REPO_ROOT)
    version = validate_version(args.version)
    tag = f"v{version}"

    if tag_exists(tag):
        raise SystemExit(f"error: tag {tag} already exists")

    prev = previous_tag()
    if prev is None:
        print(
            "warning: no previous tag reachable; the changelog will cover "
            "all history",
            file=sys.stderr,
        )
    else:
        print(f"Previous reachable tag: {prev}")

    if args.dry_run:
        print(f"[dry-run] bump pyproject.toml to {version}")
        print("[dry-run] uv lock && uv lock --check")
        print(
            "[dry-run] prepend CHANGELOG.md "
            f"({prev + '..HEAD' if prev else 'full history'})"
        )
        print(f"[dry-run] commit: chore(release): {tag}")
        if not args.no_tag:
            print(f"[dry-run] create annotated tag {tag}")
        if args.push:
            print("[dry-run] push branch and tag")
        return 0

    if working_tree_dirty():
        raise SystemExit(
            "error: working tree has uncommitted changes; commit or stash "
            "them first"
        )

    print(f"Preparing release: {tag}")
    bump_pyproject(REPO_ROOT / "pyproject.toml", version)
    sync_lockfile()
    generate_changelog(tag, prev)

    # Run pre-commit hooks on the modified files before committing, to ensure
    # that the commit passes all checks.
    updated_files = ["pyproject.toml", "uv.lock", "CHANGELOG.md"]
    run_hooks(updated_files)

    # Commit the changes and create an annotated tag for the release.
    run(["git", "add", *updated_files])
    run(["git", "commit", "-m", f"chore(release): {tag}"])

    if not args.no_tag:
        run(["git", "tag", "-a", tag, "-m", tag])

    if args.push:
        run(["git", "push", "origin", "HEAD", "--follow-tags"])
        print(f"\nPushed {tag}. The release workflow will publish it.")
    else:
        print(f"\nCreated commit and tag {tag} locally.")
        print("Push with: git push origin HEAD --follow-tags")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
