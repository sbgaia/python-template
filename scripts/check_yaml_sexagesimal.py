#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

"""Flag unquoted HH:MM values in YAML files.

YAML 1.1 reads a bare ``06:00`` as a sexagesimal integer, so Ruby's Psych
parser -- which GitHub's Dependabot uses -- sees ``21600`` where a string
was intended and rejects the file. Python parsers follow YAML 1.2 and read
the same scalar as a string, so neither the ``check-yaml`` hook nor JSON
Schema validation can catch this: they never see a number.

The scan is line based rather than parser based for that reason. Quoting
the value fixes it, and ``pretty-format-yaml`` needs ``--preserve-quotes``
so it does not strip the quotes back off.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

# Mirrors the sexagesimal pattern in Ruby's Psych scalar scanner.
SEXAGESIMAL = re.compile(r"[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+")


def sexagesimal_to_int(value: str) -> int:
    """Convert a sexagesimal scalar the way Ruby's Psych parser does.

    Args:
        value: A scalar such as ``06:00``.

    Returns:
        The integer a YAML 1.1 parser produces for that scalar.
    """
    parts = value.replace("_", "").split(":")
    return sum(
        int(part) * 60 ** abs(index - 2) for index, part in enumerate(parts)
    )


def bare_sexagesimal_values(content: str) -> list[tuple[int, str]]:
    """Find unquoted sexagesimal scalars in YAML content.

    Args:
        content: The YAML document text.

    Returns:
        A list of (line number, value) pairs, in file order.
    """
    findings: list[tuple[int, str]] = []
    for number, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.split(" #", 1)[0].strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            line = line[2:].strip()

        _, separator, value = line.partition(": ")
        candidate = value.strip() if separator else line
        if SEXAGESIMAL.fullmatch(candidate):
            findings.append((number, candidate))
    return findings


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Arguments to parse, or None to read them from the command
            line.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="YAML files to check.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Report every unquoted sexagesimal value in the given files.

    Args:
        argv: Arguments to parse, or None to read them from the command
            line.

    Returns:
        1 if any file contains an unquoted sexagesimal value, else 0.
    """
    args = parse_args(argv)
    found = False
    for path in args.paths:
        content = Path(path).read_text(encoding="utf-8")
        for number, value in bare_sexagesimal_values(content):
            print(
                f"{path}:{number}: {value} is read as the integer "
                f"{sexagesimal_to_int(value)} by YAML 1.1 parsers such as "
                f"Dependabot's; quote it as '{value}'"
            )
            found = True
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
