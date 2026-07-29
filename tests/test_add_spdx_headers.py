# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

import sys
from pathlib import Path

from scripts.add_spdx_headers import annotatable, build_command


def test_annotatable_keeps_non_empty_files(tmp_path: Path) -> None:
    populated = tmp_path / "populated.py"
    populated.write_text("x = 1\n", encoding="utf-8")

    assert annotatable([str(populated)]) == [str(populated)]


def test_annotatable_skips_zero_byte_files(tmp_path: Path) -> None:
    empty = tmp_path / "__init__.py"
    empty.touch()

    assert annotatable([str(empty)]) == []


def test_annotatable_skips_missing_paths(tmp_path: Path) -> None:
    assert annotatable([str(tmp_path / "absent.py")]) == []


def test_annotatable_skips_directories(tmp_path: Path) -> None:
    assert annotatable([str(tmp_path)]) == []


def test_build_command_uses_reuse_annotate_with_skip_flags() -> None:
    command = build_command(
        ["pkg/mod.py"],
        year="2026",
        copyright_holder="the Python Template contributors",
        license_id="BSD-2-Clause",
    )

    assert command[:4] == [sys.executable, "-m", "reuse", "annotate"]
    assert "--skip-existing" in command
    assert "--merge-copyrights" in command
    assert "--skip-unrecognised" in command
    assert command[-1] == "pkg/mod.py"


def test_build_command_passes_copyright_metadata() -> None:
    command = build_command(
        ["pkg/mod.py"],
        year="2026",
        copyright_holder="the Acme contributors",
        license_id="BSD-2-Clause",
    )

    assert command[command.index("--year") + 1] == "2026"
    assert command[command.index("--copyright") + 1] == "the Acme contributors"
    assert command[command.index("--license") + 1] == "BSD-2-Clause"
