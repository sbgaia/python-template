import subprocess
import sys
from pathlib import Path

import pytest

from scripts.bootstrap_template import (
    current_python_version,
    format_tox_env,
    normalize_minimum_python_version,
    parse_args,
    resolve_metadata,
    versions_from_minimum,
)

BOOTSTRAP_SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / ("bootstrap_template.py")
)


def test_bootstrap_template_defaults_python_version_to_interpreter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["bootstrap_template.py"])

    metadata = resolve_metadata(parse_args())

    assert metadata["minimum_python_version"] == current_python_version()


def test_bootstrap_template_rejects_unsupported_python_version() -> None:
    with pytest.raises(ValueError, match="supported template versions"):
        normalize_minimum_python_version("3.15")


def test_bootstrap_template_renames_placeholders(tmp_path: Path) -> None:
    repo_dir = tmp_path / "demo-service"
    repo_dir.mkdir()
    (repo_dir / ".devcontainer").mkdir()
    (repo_dir / "docs").mkdir()
    (repo_dir / "examples").mkdir()
    (repo_dir / "project_name").mkdir()
    (repo_dir / "tests").mkdir()

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
        "# Python Template\nClone python-template\n",
        encoding="utf-8",
    )
    (repo_dir / "docs" / "index.md").write_text(
        "# project_name\n",
        encoding="utf-8",
    )
    (repo_dir / "docs" / "api.md").write_text(
        "::: project_name\n",
        encoding="utf-8",
    )
    (repo_dir / "examples" / "say_hi.py").write_text(
        "from project_name.greeter import Greeter\n",
        encoding="utf-8",
    )
    (repo_dir / "mkdocs.yml").write_text(
        "site_name: project_name\nrepo_name: python-template\n",
        encoding="utf-8",
    )
    (repo_dir / "pyproject.toml").write_text(
        "[project]\n"
        'name = "project_name"\n'
        'description = "A simple template project."\n'
        'authors = [{ name = "Mario Potato", '
        'email = "mario.potato@univr.it" }]\n'
        "\n"
        "[tool.ruff.lint.isort]\n"
        'known-first-party = ["machine_data_model"]\n',
        encoding="utf-8",
    )
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
    assert "PYTHONPATH=demo_service" in (repo_dir / ".env").read_text(
        encoding="utf-8"
    )
    assert '"/workspaces/demo-service"' in (
        repo_dir / ".devcontainer" / "devcontainer.json"
    ).read_text(encoding="utf-8")
    assert "# Demo Service" in (repo_dir / "README.md").read_text(
        encoding="utf-8"
    )
    assert "# Demo Service" in (repo_dir / "docs" / "index.md").read_text(
        encoding="utf-8"
    )
    assert 'name = "demo-service"' in (repo_dir / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert 'known-first-party = ["demo_service"]' in (
        repo_dir / "pyproject.toml"
    ).read_text(encoding="utf-8")
    assert "site_name: demo_service" in (repo_dir / "mkdocs.yml").read_text(
        encoding="utf-8"
    )
    assert "repo_name: demo-service" in (repo_dir / "mkdocs.yml").read_text(
        encoding="utf-8"
    )
    assert "::: demo_service" in (repo_dir / "docs" / "api.md").read_text(
        encoding="utf-8"
    )


def test_bootstrap_template_uses_custom_package_name(tmp_path: Path) -> None:
    repo_dir = tmp_path / "demo-service"
    repo_dir.mkdir()
    (repo_dir / "docs").mkdir()
    (repo_dir / "project_name").mkdir()

    (repo_dir / "README.md").write_text("# Python Template\n", encoding="utf-8")
    (repo_dir / "docs" / "index.md").write_text(
        "# project_name\n", encoding="utf-8"
    )
    (repo_dir / "docs" / "api.md").write_text(
        "::: project_name\n", encoding="utf-8"
    )
    (repo_dir / "mkdocs.yml").write_text(
        "site_name: project_name\nrepo_name: python-template\n",
        encoding="utf-8",
    )
    (repo_dir / "pyproject.toml").write_text(
        "[project]\n"
        'name = "project_name"\n'
        'description = "A simple template project."\n'
        'authors = [{ name = "Mario Potato", '
        'email = "mario.potato@univr.it" }]\n'
        "\n"
        "[tool.ruff.lint.isort]\n"
        'known-first-party = ["project_name"]\n',
        encoding="utf-8",
    )

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
    assert "::: custom_pkg" in (repo_dir / "docs" / "api.md").read_text(
        encoding="utf-8"
    )


def test_bootstrap_template_uses_github_metadata(tmp_path: Path) -> None:
    repo_dir = tmp_path / "placeholder"
    repo_dir.mkdir()
    (repo_dir / ".devcontainer").mkdir()
    (repo_dir / "docs").mkdir()
    (repo_dir / "project_name").mkdir()

    (repo_dir / ".devcontainer" / "devcontainer.json").write_text(
        '{"workspaceFolder": "/workspaces/python-template"}\n',
        encoding="utf-8",
    )
    (repo_dir / "README.md").write_text("# Python Template\n", encoding="utf-8")
    (repo_dir / "docs" / "index.md").write_text(
        "# project_name\n", encoding="utf-8"
    )
    (repo_dir / "docs" / "api.md").write_text(
        "::: project_name\n", encoding="utf-8"
    )
    (repo_dir / "mkdocs.yml").write_text(
        "site_name: project_name\nrepo_name: python-template\n",
        encoding="utf-8",
    )
    (repo_dir / "pyproject.toml").write_text(
        "[project]\n"
        'name = "project_name"\n'
        'description = "A simple template project."\n'
        'authors = [{ name = "Mario Potato", '
        'email = "mario.potato@univr.it" }]\n'
        "\n"
        "[tool.ruff.lint.isort]\n"
        'known-first-party = ["project_name"]\n',
        encoding="utf-8",
    )

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
    assert 'name = "demo-service"' in (repo_dir / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert 'name = "octo-org"' in (repo_dir / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert "12345+octocat@users.noreply.github.com" in (
        repo_dir / "pyproject.toml"
    ).read_text(encoding="utf-8")


def test_bootstrap_template_updates_minimum_python_version(
    tmp_path: Path,
) -> None:
    minimum_python_version = "3.12"
    supported_versions = versions_from_minimum(minimum_python_version)
    expected_ci_matrix = ", ".join(
        f"'{version}'" for version in supported_versions
    )

    repo_dir = tmp_path / "demo-service"
    repo_dir.mkdir()
    (repo_dir / ".github" / "workflows").mkdir(parents=True)
    (repo_dir / "docs").mkdir()
    (repo_dir / "project_name").mkdir()

    (repo_dir / "README.md").write_text("# Python Template\n", encoding="utf-8")
    (repo_dir / "docs" / "index.md").write_text(
        "# project_name\n", encoding="utf-8"
    )
    (repo_dir / "docs" / "api.md").write_text(
        "::: project_name\n", encoding="utf-8"
    )
    (repo_dir / "mkdocs.yml").write_text(
        "site_name: project_name\nrepo_name: python-template\n",
        encoding="utf-8",
    )
    (repo_dir / "pyproject.toml").write_text(
        "[project]\n"
        'name = "project_name"\n'
        'description = "A simple template project."\n'
        'authors = [{ name = "Mario Potato", '
        'email = "mario.potato@univr.it" }]\n'
        'requires-python = ">=3.10,<4"\n'
        "\n"
        "[tool.pyrefly]\n"
        'python-version = "3.10.0"\n'
        "\n"
        "[tool.ruff]\n"
        'target-version = "py310"\n'
        "\n"
        "[tool.ruff.lint.isort]\n"
        'known-first-party = ["project_name"]\n',
        encoding="utf-8",
    )
    (repo_dir / "tox.ini").write_text(
        "[tox]\n"
        "env_list =\n"
        "    py{310,311,312,313}\n"
        "\n"
        "[testenv]\n"
        "commands = python -m pytest\n",
        encoding="utf-8",
    )
    (repo_dir / ".github" / "workflows" / "ci.yaml").write_text(
        "jobs:\n"
        "  test:\n"
        "    strategy:\n"
        "      matrix:\n"
        "        python-version: ['3.10', '3.11', '3.12', '3.13']\n"
        "    steps:\n"
        "    - name: Run type checks\n"
        "      if: matrix.python-version == '3.10'\n"
        "    - name: Build documentation\n"
        "      if: matrix.python-version == '3.10'\n",
        encoding="utf-8",
    )
    (repo_dir / "uv.lock").write_text(
        'version = 1\nrevision = 1\nrequires-python = ">=3.10, <4"\n',
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
    ci = (repo_dir / ".github" / "workflows" / "ci.yaml").read_text(
        encoding="utf-8"
    )
    uv_lock = (repo_dir / "uv.lock").read_text(encoding="utf-8")

    assert f'requires-python = ">={minimum_python_version},<4"' in pyproject
    assert f'python-version = "{minimum_python_version}.0"' in pyproject
    assert 'target-version = "py312"' in pyproject
    assert f"    {format_tox_env(supported_versions)}" in tox
    assert f"python-version: [{expected_ci_matrix}]" in ci
    assert f"matrix.python-version == '{minimum_python_version}'" in ci
    assert f'requires-python = ">={minimum_python_version}, <4"' in uv_lock
