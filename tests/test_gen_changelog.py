# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from scripts.gen_changelog import CONFIG, build_command, git_cliff_executable

if TYPE_CHECKING:
    from pathlib import Path


def test_build_command_passes_the_config_and_forwards_arguments() -> None:
    command = build_command(["--tag", "v0.1.0", "--prepend", "CHANGELOG.md"])

    assert command[1:] == [
        "--config",
        str(CONFIG),
        "--tag",
        "v0.1.0",
        "--prepend",
        "CHANGELOG.md",
    ]


def test_git_cliff_executable_prefers_the_interpreter_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    binary = tmp_path / "git-cliff"
    binary.touch()
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python"))

    assert git_cliff_executable() == str(binary)


def test_git_cliff_executable_finds_the_windows_binary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    binary = tmp_path / "git-cliff.exe"
    binary.touch()
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python.exe"))

    assert git_cliff_executable() == str(binary)


def test_git_cliff_executable_falls_back_to_the_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    binary = tmp_path / "elsewhere" / "git-cliff"
    binary.parent.mkdir()
    binary.touch()
    binary.chmod(0o755)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python"))
    monkeypatch.setenv("PATH", str(binary.parent))

    assert git_cliff_executable() == str(binary)


def test_git_cliff_executable_reports_a_missing_binary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python"))
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))

    with pytest.raises(SystemExit, match="git-cliff"):
        git_cliff_executable()
