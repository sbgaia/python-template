# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.bootstrap_template import (
    format_tox_env,
    normalize_distribution_name,
    normalize_minimum_python_version,
    parse_args,
    resolve_metadata,
    versions_from_minimum,
)

BOOTSTRAP_SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "bootstrap_template.py"
)
API_TEMPLATE = "```{automodule} project_name\n```\n"
CONF_TEMPLATE = (
    'project = "project_name"\n'
    'author = "Mario Potato"\n'
    'copyright = "2026, Mario Potato"\n'
    'html_title = "project_name documentation"\n'
)


def write_docs_files(repo_dir: Path) -> None:
    """Write the minimal docs files used by bootstrap tests."""
    (repo_dir / "docs").mkdir(exist_ok=True)
    (repo_dir / "docs" / "index.md").write_text(
        "# project_name\n", encoding="utf-8"
    )
    (repo_dir / "docs" / "api.md").write_text(API_TEMPLATE, encoding="utf-8")
    (repo_dir / "docs" / "conf.py").write_text(CONF_TEMPLATE, encoding="utf-8")


def write_pyproject(repo_dir: Path, *, include_python: bool = False) -> None:
    """Write minimal pyproject metadata for bootstrap tests."""
    python_config = ""
    if include_python:
        python_config = (
            'requires-python = ">=3.10,<4"\n'
            "\n"
            "[tool.pyrefly]\n"
            'python-version = "3.10.0"\n'
            "\n"
            "[tool.ruff]\n"
            'target-version = "py310"\n'
            "\n"
        )

    (repo_dir / "pyproject.toml").write_text(
        "[project]\n"
        'name = "project_name"\n'
        'description = "A simple template project."\n'
        'authors = [{ name = "Mario Potato", '
        'email = "mario.potato@univr.it" }]\n'
        f"{python_config}"
        "\n"
        "[tool.ruff.lint.isort]\n"
        'known-first-party = ["project_name"]\n'
        "\n"
        "[tool.coverage.run]\n"
        'source = ["project_name"]\n',
        encoding="utf-8",
    )


def test_bootstrap_template_leaves_python_version_unconfigured_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["bootstrap_template.py"])

    metadata = resolve_metadata(parse_args())

    assert "minimum_python_version" not in metadata


def test_bootstrap_template_rejects_unsupported_python_version() -> None:
    with pytest.raises(ValueError, match="supported template versions"):
        normalize_minimum_python_version("3.15")


def test_bootstrap_template_normalizes_distribution_names() -> None:
    assert normalize_distribution_name("Demo_Service") == "demo-service"
    assert normalize_distribution_name("demo.service") == "demo-service"


def test_bootstrap_template_renames_placeholders(tmp_path: Path) -> None:
    repo_dir = tmp_path / "demo-service"
    repo_dir.mkdir()
    (repo_dir / ".devcontainer").mkdir()
    (repo_dir / "examples").mkdir()
    (repo_dir / "project_name").mkdir()
    (repo_dir / "tests").mkdir()
    (repo_dir / "project_name" / "__init__.py").write_text(
        "from project_name.greeter import Greeter\n",
        encoding="utf-8",
    )

    (repo_dir / ".env").write_text(
        "PYTHONPATH=project_name\nPROJECT_SOURCE_DIR=project_name\n",
        encoding="utf-8",
    )
    (repo_dir / ".devcontainer" / "devcontainer.json").write_text(
        '{"workspaceFolder": "/workspaces/python-template"}\n',
        encoding="utf-8",
    )
    (repo_dir / ".pre-commit-config.yaml").write_text(
        "files: ^project_name/.+\n",
        encoding="utf-8",
    )
    (repo_dir / "Dockerfile").write_text(
        "COPY project_name/ project_name\n",
        encoding="utf-8",
    )
    (repo_dir / "README.md").write_text(
        "# Python Template\nClone python-template\nUse project_name\n",
        encoding="utf-8",
    )
    write_docs_files(repo_dir)
    (repo_dir / "examples" / "say_hi.py").write_text(
        "from project_name.greeter import Greeter\n",
        encoding="utf-8",
    )
    write_pyproject(repo_dir)
    (repo_dir / "tests" / "test_greeter.py").write_text(
        "from project_name.greeter import Greeter\n",
        encoding="utf-8",
    )
    (repo_dir / "tox.ini").write_text(
        "commands = python -m pytest --cov=project_name\n",
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            str(BOOTSTRAP_SCRIPT),
            "demo-service",
            "--author",
            "Ada Lovelace",
            "--author-email",
            "ada@example.com",
            "--description",
            "Demo service.",
        ],
        cwd=repo_dir,
        check=True,
    )

    assert not (repo_dir / "project_name").exists()
    assert (repo_dir / "demo_service").exists()
    assert "from demo_service.greeter import Greeter" in (
        repo_dir / "demo_service" / "__init__.py"
    ).read_text(encoding="utf-8")
    assert "PYTHONPATH=demo_service" in (repo_dir / ".env").read_text(
        encoding="utf-8"
    )
    assert '"/workspaces/demo-service"' in (
        repo_dir / ".devcontainer" / "devcontainer.json"
    ).read_text(encoding="utf-8")

    readme = (repo_dir / "README.md").read_text(encoding="utf-8")
    assert "# Demo Service" in readme
    assert "demo-service" in readme
    assert "demo_service" in readme
    assert "# Demo Service" in (repo_dir / "docs" / "index.md").read_text(
        encoding="utf-8"
    )

    pyproject = (repo_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "demo-service"' in pyproject
    assert 'known-first-party = ["demo_service"]' in pyproject
    assert 'source = ["demo_service"]' in pyproject

    docs_conf = (repo_dir / "docs" / "conf.py").read_text(encoding="utf-8")
    assert 'project = "Demo Service"' in docs_conf
    assert 'author = "Ada Lovelace"' in docs_conf
    assert 'html_title = "Demo Service documentation"' in docs_conf
    assert "automodule} demo_service" in (
        repo_dir / "docs" / "api.md"
    ).read_text(encoding="utf-8")


def test_bootstrap_template_uses_custom_package_name(tmp_path: Path) -> None:
    repo_dir = tmp_path / "demo-service"
    repo_dir.mkdir()
    (repo_dir / "project_name").mkdir()

    (repo_dir / "README.md").write_text("# Python Template\n", encoding="utf-8")
    write_docs_files(repo_dir)
    write_pyproject(repo_dir)

    subprocess.run(
        [
            sys.executable,
            str(BOOTSTRAP_SCRIPT),
            "demo-service",
            "--package-name",
            "custom_pkg",
        ],
        cwd=repo_dir,
        check=True,
    )

    assert (repo_dir / "custom_pkg").exists()
    assert 'known-first-party = ["custom_pkg"]' in (
        repo_dir / "pyproject.toml"
    ).read_text(encoding="utf-8")
    assert "automodule} custom_pkg" in (repo_dir / "docs" / "api.md").read_text(
        encoding="utf-8"
    )


def test_bootstrap_template_uses_github_metadata(tmp_path: Path) -> None:
    repo_dir = tmp_path / "placeholder"
    repo_dir.mkdir()
    (repo_dir / ".devcontainer").mkdir()
    (repo_dir / "project_name").mkdir()

    (repo_dir / ".devcontainer" / "devcontainer.json").write_text(
        '{"workspaceFolder": "/workspaces/python-template"}\n',
        encoding="utf-8",
    )
    (repo_dir / "README.md").write_text("# Python Template\n", encoding="utf-8")
    write_docs_files(repo_dir)
    write_pyproject(repo_dir)

    env = {
        "GITHUB_REPOSITORY": "octo-org/demo-service",
        "GITHUB_REPOSITORY_OWNER": "octo-org",
        "GITHUB_ACTOR": "octocat",
        "GITHUB_ACTOR_ID": "12345",
    }

    subprocess.run(
        [
            sys.executable,
            str(BOOTSTRAP_SCRIPT),
            "--from-github",
        ],
        cwd=repo_dir,
        check=True,
        env=env,
    )

    assert (repo_dir / "demo_service").exists()
    pyproject = (repo_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "demo-service"' in pyproject
    assert 'name = "octo-org"' in pyproject
    assert "12345+octocat@users.noreply.github.com" in pyproject
    assert 'author = "octo-org"' in (repo_dir / "docs" / "conf.py").read_text(
        encoding="utf-8"
    )


def test_bootstrap_template_updates_minimum_python_version(
    tmp_path: Path,
) -> None:
    minimum_python_version = "3.12"
    supported_versions = versions_from_minimum(minimum_python_version)
    repo_dir = tmp_path / "demo-service"
    repo_dir.mkdir()
    (repo_dir / ".github" / "workflows").mkdir(parents=True)
    (repo_dir / "project_name").mkdir()

    (repo_dir / "README.md").write_text("# Python Template\n", encoding="utf-8")
    write_docs_files(repo_dir)
    write_pyproject(repo_dir, include_python=True)
    (repo_dir / "tox.ini").write_text(
        "[tox]\n"
        "env_list =\n"
        "    py{310,311,312,313}\n"
        "\n"
        "[testenv]\n"
        "commands = python -m pytest\n",
        encoding="utf-8",
    )
    tests_workflow = (
        "env:\n"
        "  PYTHON_VERSION: '3.10'\n"
        "jobs:\n"
        "  test:\n"
        "    strategy:\n"
        "      matrix:\n"
        "        include:\n"
        "        - python-version: '3.10'\n"
        "          tox-env: py310\n"
        "        - python-version: '3.11'\n"
        "          tox-env: py311\n"
        "        - python-version: '3.12'\n"
        "          tox-env: py312\n"
        "        - python-version: '3.13'\n"
        "          tox-env: py313\n"
        "    steps:\n"
        "    - name: Run tests\n"
        "      if: matrix.python-version == '3.10'\n"
    )
    coverage_workflow = (
        "env:\n"
        "  PYTHON_VERSION: '3.10'\n"
        "jobs:\n"
        "  coverage:\n"
        "    steps:\n"
        "    - uses: ./.github/actions/setup-python-uv\n"
        "      with:\n"
        "        python-version: ${{ env.PYTHON_VERSION }}\n"
    )
    quality_workflow = (
        "env:\n"
        "  PYTHON_VERSION: '3.10'\n"
        "jobs:\n"
        "  type:\n"
        "    steps:\n"
        "    - uses: ./.github/actions/setup-python-uv\n"
        "      with:\n"
        "        python-version: ${{ env.PYTHON_VERSION }}\n"
    )
    docker_workflow = (
        "jobs:\n"
        "  docker:\n"
        "    steps:\n"
        "    - run: docker build --pull -t python-template:ci .\n"
        "    - run: docker run --rm python-template:ci uv run "
        'python -c "import project_name"\n'
    )
    (repo_dir / ".github" / "workflows" / "tests.yaml").write_text(
        tests_workflow,
        encoding="utf-8",
    )
    (repo_dir / ".github" / "workflows" / "coverage.yaml").write_text(
        coverage_workflow,
        encoding="utf-8",
    )
    (repo_dir / ".github" / "workflows" / "quality.yaml").write_text(
        quality_workflow,
        encoding="utf-8",
    )
    (repo_dir / ".github" / "workflows" / "docker.yaml").write_text(
        docker_workflow,
        encoding="utf-8",
    )
    (repo_dir / "uv.lock").write_text(
        'version = 1\nrevision = 1\nname = "project-name"\n'
        'requires-python = ">=3.10, <4"\n',
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            str(BOOTSTRAP_SCRIPT),
            "demo-service",
            "--minimum-python-version",
            minimum_python_version,
        ],
        cwd=repo_dir,
        check=True,
    )

    pyproject = (repo_dir / "pyproject.toml").read_text(encoding="utf-8")
    tox = (repo_dir / "tox.ini").read_text(encoding="utf-8")
    tests_ci = (repo_dir / ".github" / "workflows" / "tests.yaml").read_text(
        encoding="utf-8"
    )
    coverage_ci = (
        repo_dir / ".github" / "workflows" / "coverage.yaml"
    ).read_text(encoding="utf-8")
    quality_ci = (
        repo_dir / ".github" / "workflows" / "quality.yaml"
    ).read_text(encoding="utf-8")
    docker_ci = (repo_dir / ".github" / "workflows" / "docker.yaml").read_text(
        encoding="utf-8"
    )
    uv_lock = (repo_dir / "uv.lock").read_text(encoding="utf-8")

    assert f'requires-python = ">={minimum_python_version},<4"' in pyproject
    assert f'python-version = "{minimum_python_version}.0"' in pyproject
    assert 'target-version = "py312"' in pyproject
    assert f"    {format_tox_env(supported_versions)}" in tox
    assert f"PYTHON_VERSION: '{minimum_python_version}'" in tests_ci
    assert f"matrix.python-version == '{minimum_python_version}'" in tests_ci
    for version in supported_versions:
        assert f"- python-version: '{version}'" in tests_ci
        assert f"tox-env: {format_tox_env((version,))}" in tests_ci
    assert "python-version: '3.10'" not in tests_ci
    assert f"PYTHON_VERSION: '{minimum_python_version}'" in coverage_ci
    assert "python-version: ${{ env.PYTHON_VERSION }}" in coverage_ci
    assert f"PYTHON_VERSION: '{minimum_python_version}'" in quality_ci
    assert "python-version: ${{ env.PYTHON_VERSION }}" in quality_ci
    assert "demo-service:ci" in docker_ci
    assert "import demo_service" in docker_ci
    assert "python-template" not in docker_ci
    assert "project_name" not in docker_ci
    assert 'name = "demo-service"' in uv_lock
    assert f'requires-python = ">={minimum_python_version}, <4"' in uv_lock
