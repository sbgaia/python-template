# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from scripts.gen_changelog import (
    CONFIG,
    build_command,
    git_cliff_executable,
    normalize,
    output_path,
)

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


@pytest.mark.parametrize(
    "argv",
    [
        ["--tag", "v0.1.0", "-o", "CHANGELOG.md"],
        ["--tag", "v0.1.0", "--output", "CHANGELOG.md"],
        ["--tag", "v0.1.0", "-p", "CHANGELOG.md"],
        ["--tag", "v0.1.0", "--prepend", "CHANGELOG.md"],
        ["--output=CHANGELOG.md"],
        ["--prepend=CHANGELOG.md"],
    ],
)
def test_output_path_finds_the_written_file(argv: list[str]) -> None:
    found = output_path(argv)

    assert found is not None
    assert found.name == "CHANGELOG.md"


@pytest.mark.parametrize(
    "argv", [["--tag", "v0.1.0"], [], ["--tag", "v0.1.0", "-o"]]
)
def test_output_path_is_none_without_a_target_file(argv: list[str]) -> None:
    """A bare -o writes to stdout, so there is nothing to normalize."""
    assert output_path(argv) is None


def test_normalize_reduces_trailing_blank_lines_to_one_newline(
    tmp_path: Path,
) -> None:
    path = tmp_path / "CHANGELOG.md"
    path.write_text("# Changelog\n\n## 0.1.0\n\n- [abc] x\n\n\n", "utf-8")

    normalize(path)

    assert path.read_text("utf-8") == "# Changelog\n\n## 0.1.0\n\n- [abc] x\n"


def test_normalize_strips_trailing_whitespace_per_line(tmp_path: Path) -> None:
    path = tmp_path / "CHANGELOG.md"
    path.write_text("# Changelog  \n\n- [abc] x \n", encoding="utf-8")

    normalize(path)

    assert path.read_text(encoding="utf-8") == "# Changelog\n\n- [abc] x\n"


def test_normalize_keeps_blank_lines_between_sections(tmp_path: Path) -> None:
    """The blank line before a heading is what mdformat requires."""
    content = "# Changelog\n\n## 0.2.0\n\n- [abc] x\n\n## 0.1.0\n\n- [def] y\n"
    path = tmp_path / "CHANGELOG.md"
    path.write_text(content, encoding="utf-8")

    normalize(path)

    assert path.read_text(encoding="utf-8") == content


def test_normalize_ignores_a_missing_file(tmp_path: Path) -> None:
    """git-cliff may fail before creating the file; that is its error."""
    normalize(tmp_path / "absent.md")


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
