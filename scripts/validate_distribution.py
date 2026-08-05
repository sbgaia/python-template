#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

"""Build the project distribution and verify the wheel imports cleanly."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_PACKAGE = "project_name"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--package",
        default=DEFAULT_PACKAGE,
        help="Import package name to verify from the built wheel.",
    )
    parser.add_argument(
        "--dist-dir",
        default="dist",
        help="Directory where build artifacts should be written.",
    )
    return parser.parse_args()


def run(command: list[str], *, cwd: Path | None = None) -> None:
    """Run a command and fail immediately on errors."""
    print("+ " + " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def build_distribution(dist_dir: Path) -> Path:
    """Build sdist and wheel artifacts and return the wheel path."""
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True)

    run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--sdist",
            "--wheel",
            "--outdir",
            str(dist_dir),
        ]
    )

    wheels = sorted(dist_dir.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(
            f"Expected exactly one wheel in {dist_dir}, found {len(wheels)}."
        )
    if not any(dist_dir.glob("*.tar.gz")):
        raise RuntimeError(f"Expected an sdist artifact in {dist_dir}.")
    return wheels[0]


def verify_wheel_import(wheel: Path, package: str) -> None:
    """Import the built wheel away from the source checkout."""
    wheel_path = wheel.resolve()
    import_code = (
        "import importlib; "
        "import sys; "
        f"sys.path.insert(0, {str(wheel_path)!r}); "
        f"module = importlib.import_module({package!r}); "
        f"assert module.__name__ == {package!r}"
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        run([sys.executable, "-c", import_code], cwd=Path(tmp_dir))


def main() -> int:
    """Build and validate the project distribution."""
    args = parse_args()
    wheel = build_distribution(Path(args.dist_dir))
    verify_wheel_import(wheel, args.package)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
