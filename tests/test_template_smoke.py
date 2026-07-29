# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

import os
import shutil
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

import pytest

RUN_TEMPLATE_SMOKE = os.environ.get("RUN_TEMPLATE_SMOKE") == "1"
IGNORED_COPY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "dist",
    "docs/_build",
    "htmlcov",
}
PLACEHOLDER_CHECK_PATHS = (
    ".github/workflows/coverage.yaml",
    ".github/workflows/docker.yaml",
    ".github/workflows/documentation.yaml",
    ".github/workflows/package.yaml",
    ".github/workflows/quality.yaml",
    ".github/workflows/release.yaml",
    ".github/workflows/security.yaml",
    ".github/workflows/template-smoke.yaml",
    ".github/workflows/tests.yaml",
    "README.md",
    "REUSE.toml",
    "cliff.toml",
    "docs/api.md",
    "docs/conf.py",
    "docs/documentation.md",
    "docs/index.md",
    "docs/template.md",
    "docs/usage.md",
    "pyproject.toml",
    "scripts/add_spdx_headers.py",
    "scripts/gen_changelog.py",
    "scripts/release.py",
    "tox.ini",
)


def ignore_template_artifacts(
    directory: str,
    names: Iterable[str],
) -> set[str]:
    """Return generated paths that should not be copied into smoke tests."""
    current_dir = Path(directory)
    ignored = set()
    for name in names:
        relative_name = name
        if current_dir.name == "docs":
            relative_name = f"docs/{name}"
        if relative_name in IGNORED_COPY_NAMES or name.endswith(".egg-info"):
            ignored.add(name)
    return ignored


def run(command: list[str], *, cwd: Path) -> None:
    """Run a subprocess in the generated project."""
    subprocess.run(command, cwd=cwd, check=True)


@pytest.mark.template_smoke
@pytest.mark.skipif(
    not RUN_TEMPLATE_SMOKE,
    reason="set RUN_TEMPLATE_SMOKE=1 to run the generated-project smoke test",
)
def test_generated_project_bootstraps_and_builds(tmp_path: Path) -> None:
    source_repo = Path(__file__).resolve().parents[1]
    generated_repo = tmp_path / "demo-service"
    shutil.copytree(
        source_repo,
        generated_repo,
        ignore=ignore_template_artifacts,
    )

    run(
        [
            sys.executable,
            str(generated_repo / "scripts" / "bootstrap_template.py"),
            "demo-service",
            "--author",
            "Ada Lovelace",
            "--author-email",
            "ada@example.com",
            "--description",
            "Generated project smoke test.",
        ],
        cwd=generated_repo,
    )

    run(
        ["uv", "sync", "--locked", "--extra", "dev", "--extra", "docs"],
        cwd=generated_repo,
    )
    run(
        [
            "uv",
            "run",
            "python",
            "-c",
            "from demo_service import Greeter; "
            "assert Greeter('CI').greet() == 'Hello, CI!'",
        ],
        cwd=generated_repo,
    )
    run(["uv", "run", "pytest", "tests/test_greeter.py"], cwd=generated_repo)
    run(
        ["uv", "run", "tox", "run", "--skip-pkg-install", "-e", "docs"],
        cwd=generated_repo,
    )
    run(
        ["uv", "run", "tox", "run", "--skip-pkg-install", "-e", "build"],
        cwd=generated_repo,
    )

    for relative_path in PLACEHOLDER_CHECK_PATHS:
        content = (generated_repo / relative_path).read_text(encoding="utf-8")
        assert "project_name" not in content, relative_path
        assert "python-template" not in content, relative_path

    reuse_toml = (generated_repo / "REUSE.toml").read_text(encoding="utf-8")
    assert "the Demo Service contributors" in reuse_toml
    assert "the Python Template contributors" not in reuse_toml

    package_modules = sorted(
        path
        for path in (generated_repo / "demo_service").glob("*.py")
        if path.stat().st_size > 0
    )
    assert package_modules

    for module in package_modules:
        content = module.read_text(encoding="utf-8")
        # REUSE-IgnoreStart
        assert "SPDX-License-Identifier: BSD-2-Clause" in content, str(module)
        # REUSE-IgnoreEnd
        assert "the Demo Service contributors" in content, str(module)
        assert "the Python Template contributors" not in content, str(module)
