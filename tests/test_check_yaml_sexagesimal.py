# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from scripts.check_yaml_sexagesimal import (
    bare_sexagesimal_values,
    main,
    sexagesimal_to_int,
)

if TYPE_CHECKING:
    from pathlib import Path

DEPENDABOT = """version: 2
updates:
- package-ecosystem: uv
  directory: /
  schedule:
    interval: weekly
    day: monday
    time: 06:00
    timezone: Europe/Rome
"""


@pytest.mark.parametrize(
    ("value", "expected"),
    [("06:00", 21600), ("06:30", 23400), ("07:00", 25200), ("1:02:03", 3723)],
)
def test_sexagesimal_to_int_matches_the_ruby_result(
    value: str, expected: int
) -> None:
    assert sexagesimal_to_int(value) == expected


def test_bare_sexagesimal_values_flags_an_unquoted_time() -> None:
    assert bare_sexagesimal_values(DEPENDABOT) == [(8, "06:00")]


def test_bare_sexagesimal_values_accepts_a_quoted_time() -> None:
    assert bare_sexagesimal_values(DEPENDABOT.replace("06:00", "'06:00'")) == []


def test_bare_sexagesimal_values_flags_a_sequence_item() -> None:
    assert bare_sexagesimal_values("times:\n- 06:00\n") == [(2, "06:00")]


def test_bare_sexagesimal_values_reports_every_line() -> None:
    content = "a: 06:00\nb: 06:30\nc: '07:00'\n"

    assert bare_sexagesimal_values(content) == [(1, "06:00"), (2, "06:30")]


@pytest.mark.parametrize(
    "content",
    [
        "version: 2\n",
        "timeout-minutes: 20\n",
        "timezone: Europe/Rome\n",
        "python-version: '3.10'\n",
        "cron: '0 6 * * 1'\n",
        "url: http://example.com:8080\n",
        "# time: 06:00\n",
        "schedule:\n",
        # 60 is out of range, so a YAML 1.1 parser leaves it a string.
        "time: 06:60\n",
    ],
)
def test_bare_sexagesimal_values_ignores_unambiguous_scalars(
    content: str,
) -> None:
    assert bare_sexagesimal_values(content) == []


def test_bare_sexagesimal_values_ignores_a_trailing_comment() -> None:
    assert bare_sexagesimal_values("time: '06:00' # daily\n") == []


def test_main_reports_the_offending_file_and_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "dependabot.yml"
    path.write_text(DEPENDABOT, encoding="utf-8")

    assert main([str(path)]) == 1

    output = capsys.readouterr().out
    assert f"{path}:8" in output
    assert "21600" in output
    assert "'06:00'" in output


def test_main_accepts_a_quoted_file(tmp_path: Path) -> None:
    path = tmp_path / "dependabot.yml"
    path.write_text(
        DEPENDABOT.replace("06:00", "'06:00'"),
        encoding="utf-8",
    )

    assert main([str(path)]) == 0
