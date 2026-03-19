import subprocess
import sys
from pathlib import Path


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
            str(
                Path(
                    "/home/sebastiano/python-template/scripts/bootstrap_template.py"
                )
            ),
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
    assert "# Demo Service" in (
        repo_dir / "docs" / "index.md"
    ).read_text(encoding="utf-8")
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
            str(
                Path(
                    "/home/sebastiano/python-template/scripts/bootstrap_template.py"
                )
            ),
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
