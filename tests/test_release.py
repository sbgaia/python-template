# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.release import (
    REPO_ROOT,
    bump_pyproject,
    changelog_range,
    generate_changelog,
    main,
    previous_tag,
    sync_lockfile,
    tag_exists,
    validate_version,
    working_tree_dirty,
)

PYPROJECT = """[project]
name = "project_name"
version = "0.0.0"
description = "A simple template project."
"""


class FakeRunner:
    """Records commands and replays canned results."""

    def __init__(
        self,
        results: dict[str, subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self.commands: list[list[str]] = []
        self.results = results or {}

    def __call__(
        self,
        command: list[str],
        *,
        check: bool = True,
        capture: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        self.commands.append(command)
        key = " ".join(command)
        result = self.results.get(key)
        if result is None:
            return subprocess.CompletedProcess(command, 0, "", "")
        return result


REPO_CONFIG = {
    # Written to the repo config rather than passed per command, so callers
    # can commit and tag without a global git identity.
    "user.email": "a@b",
    "user.name": "a",
    # Ambient signing settings would otherwise make commits and tags here
    # depend on the contributor's keys being present and unlocked.
    "commit.gpgsign": "false",
    "tag.gpgSign": "false",
}


def git_repo(tmp_path: Path) -> Path:
    """Create a throwaway git repo with one commit.

    The repo is configured to be independent of the ambient git config, so
    the tests behave the same for every contributor and on CI.
    """
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for key, value in REPO_CONFIG.items():
        subprocess.run(["git", "config", key, value], cwd=tmp_path, check=True)
    (tmp_path / "file.txt").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    return tmp_path


@pytest.mark.parametrize("version", ["0.1.0", "1.2.3", "10.0.1", "1.0.0-rc1"])
def test_validate_version_accepts_valid_versions(version: str) -> None:
    assert validate_version(version) == version


@pytest.mark.parametrize("version", ["1.2", "v1.2.3", "abc", "", "1.2.3-"])
def test_validate_version_rejects_invalid_versions(version: str) -> None:
    with pytest.raises(ValueError):
        validate_version(version)


def test_bump_pyproject_replaces_version(tmp_path: Path) -> None:
    path = tmp_path / "pyproject.toml"
    path.write_text(PYPROJECT, encoding="utf-8")

    bump_pyproject(path, "0.1.0")

    assert 'version = "0.1.0"' in path.read_text(encoding="utf-8")
    assert 'version = "0.0.0"' not in path.read_text(encoding="utf-8")


def test_bump_pyproject_leaves_other_metadata_alone(tmp_path: Path) -> None:
    path = tmp_path / "pyproject.toml"
    path.write_text(PYPROJECT, encoding="utf-8")

    bump_pyproject(path, "0.1.0")

    content = path.read_text(encoding="utf-8")
    assert 'name = "project_name"' in content
    assert 'description = "A simple template project."' in content


def test_bump_pyproject_raises_without_a_version_line(tmp_path: Path) -> None:
    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "x"\n', encoding="utf-8")

    with pytest.raises(ValueError):
        bump_pyproject(path, "0.1.0")


def test_tag_exists_is_false_for_unknown_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(git_repo(tmp_path))

    assert tag_exists("v9.9.9") is False


def test_tag_exists_is_true_for_created_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = git_repo(tmp_path)
    subprocess.run(
        ["git", "tag", "-a", "v0.1.0", "-m", "v0.1.0"], cwd=repo, check=True
    )
    monkeypatch.chdir(repo)

    assert tag_exists("v0.1.0") is True


def test_working_tree_dirty_is_false_when_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(git_repo(tmp_path))

    assert working_tree_dirty() is False


def test_working_tree_dirty_is_true_with_modifications(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = git_repo(tmp_path)
    (repo / "file.txt").write_text("changed\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    assert working_tree_dirty() is True


def test_previous_tag_is_none_without_tags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(git_repo(tmp_path))

    assert previous_tag() is None


def test_previous_tag_returns_most_recent_reachable_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = git_repo(tmp_path)
    subprocess.run(
        ["git", "tag", "-a", "v0.1.0", "-m", "v0.1.0"], cwd=repo, check=True
    )
    monkeypatch.chdir(repo)

    assert previous_tag() == "v0.1.0"


def test_main_operates_from_the_repository_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The release runs against the repo regardless of the caller's cwd."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["release.py", "99.0.0", "--dry-run"])

    assert main() == 0
    assert Path.cwd() == REPO_ROOT


def test_sync_lockfile_locks_then_verifies() -> None:
    runner = FakeRunner()

    sync_lockfile(runner=runner)

    assert runner.commands == [["uv", "lock"], ["uv", "lock", "--check"]]


def test_changelog_range_is_empty_without_a_previous_tag() -> None:
    assert changelog_range(None) == []


def test_changelog_range_spans_from_previous_tag_to_head() -> None:
    assert changelog_range("v0.1.0") == ["v0.1.0..HEAD"]


def test_generate_changelog_regenerates_when_there_is_no_previous_tag() -> None:
    runner = FakeRunner()

    generate_changelog("v0.1.0", None, runner=runner)

    command = runner.commands[0]
    assert "-o" in command
    assert "--prepend" not in command
    assert command[command.index("-o") + 1] == "CHANGELOG.md"


def test_generate_changelog_prepends_when_a_previous_tag_exists() -> None:
    runner = FakeRunner()

    generate_changelog("v0.1.0", "v0.0.9", runner=runner)

    command = runner.commands[0]
    assert "--prepend" in command
    assert "-o" not in command
    assert "v0.0.9..HEAD" in command
