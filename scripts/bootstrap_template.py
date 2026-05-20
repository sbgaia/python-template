#!/usr/bin/env python3
"""Bootstrap a repository created from this template."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

PLACEHOLDER_PACKAGE = "project_name"
PLACEHOLDER_REPOSITORY = "python-template"
PLACEHOLDER_AUTHOR = "Mario Potato"
PLACEHOLDER_AUTHOR_EMAIL = "mario.potato@univr.it"
PLACEHOLDER_DESCRIPTION = "A simple template project."
DEFAULT_MINIMUM_PYTHON_VERSION = "3.10"
SUPPORTED_PYTHON_VERSIONS = ("3.10", "3.11", "3.12", "3.13", "3.14")

PACKAGE_FILES = (
    Path(".env"),
    Path(".pre-commit-config.yaml"),
    Path("Dockerfile"),
    Path("docs/api.md"),
    Path("examples/say_hi.py"),
    Path("mkdocs.yml"),
    Path("tests/test_greeter.py"),
    Path("tox.ini"),
)
REPOSITORY_FILES = (
    Path(".devcontainer/devcontainer.json"),
    Path("mkdocs.yml"),
    Path("README.md"),
)
DOCS_INDEX = Path("docs/index.md")
PACKAGE_DIR = Path(PLACEHOLDER_PACKAGE)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "repository_name",
        nargs="?",
        help=(
            "Repository/distribution name. Defaults to GitHub metadata "
            "or the current directory."
        ),
    )
    parser.add_argument(
        "--package-name",
        help=(
            "Python import package name. Defaults to repository name with "
            "dashes replaced by underscores."
        ),
    )
    parser.add_argument(
        "--project-title",
        help=(
            "Human-readable project title. Defaults to a title-cased "
            "repository name."
        ),
    )
    parser.add_argument(
        "--author",
        default=PLACEHOLDER_AUTHOR,
        help="Author name to write into project metadata.",
    )
    parser.add_argument(
        "--author-email",
        default=PLACEHOLDER_AUTHOR_EMAIL,
        help="Author email to write into project metadata.",
    )
    parser.add_argument(
        "--description",
        default=PLACEHOLDER_DESCRIPTION,
        help="Package description to write into project metadata.",
    )
    parser.add_argument(
        "--minimum-python-version",
        "--min-python-version",
        default=DEFAULT_MINIMUM_PYTHON_VERSION,
        help=(
            "Minimum supported Python version. Supported values: "
            f"{', '.join(SUPPORTED_PYTHON_VERSIONS)}."
        ),
    )
    parser.add_argument(
        "--from-github",
        action="store_true",
        help=(
            "Infer repository metadata from GitHub Actions environment "
            "variables."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned changes without modifying files.",
    )
    return parser.parse_args()


def normalize_minimum_python_version(version: str) -> str:
    """Normalize and validate the minimum supported Python version."""
    match = re.fullmatch(r"3\.(\d{1,2})(?:\.\d+)?", version.strip())
    if not match:
        raise ValueError(
            "minimum_python_version must use a major.minor value like 3.10."
        )

    normalized = f"3.{int(match.group(1))}"
    if normalized not in SUPPORTED_PYTHON_VERSIONS:
        supported = ", ".join(SUPPORTED_PYTHON_VERSIONS)
        raise ValueError(
            "minimum_python_version must be one of the supported template "
            f"versions: {supported}."
        )
    return normalized


def python_env_name(version: str) -> str:
    """Convert a Python version to the tox/Ruff compact version form."""
    major, minor = version.split(".")
    return f"py{major}{minor}"


def versions_from_minimum(minimum_version: str) -> tuple[str, ...]:
    """Return all template-supported Python versions from a minimum version."""
    minimum_index = SUPPORTED_PYTHON_VERSIONS.index(minimum_version)
    return SUPPORTED_PYTHON_VERSIONS[minimum_index:]


def format_tox_env(versions: tuple[str, ...]) -> str:
    """Format Python versions for tox env_list."""
    env_names = [
        python_env_name(version).removeprefix("py") for version in versions
    ]
    if len(env_names) == 1:
        return f"py{env_names[0]}"
    return f"py{{{','.join(env_names)}}}"


def github_noreply_email() -> str:
    """Build a GitHub noreply email address from available environment data."""
    actor = os.environ.get("GITHUB_ACTOR", "").strip()
    actor_id = os.environ.get("GITHUB_ACTOR_ID", "").strip()
    if actor and actor_id:
        return f"{actor_id}+{actor}@users.noreply.github.com"
    if actor:
        return f"{actor}@users.noreply.github.com"
    return PLACEHOLDER_AUTHOR_EMAIL


def resolve_metadata(args: argparse.Namespace) -> dict[str, str]:
    """Resolve bootstrap metadata from args and GitHub context."""
    repository_name = (
        args.repository_name or os.environ.get("GITHUB_REPOSITORY", "")
    ).strip()
    if "/" in repository_name:
        repository_name = repository_name.rsplit("/", maxsplit=1)[-1]
    if not repository_name:
        repository_name = Path.cwd().name

    package_name = (
        args.package_name or repository_name.replace("-", "_")
    ).strip()
    project_title = (
        args.project_title
        or repository_name.replace("-", " ").replace("_", " ").title()
    ).strip()

    author = args.author
    author_email = args.author_email
    if args.from_github:
        author = os.environ.get("GITHUB_REPOSITORY_OWNER", "").strip() or author
        author_email = github_noreply_email()

    minimum_python_version = normalize_minimum_python_version(
        str(args.minimum_python_version)
    )

    return {
        "repository_name": repository_name,
        "package_name": package_name,
        "project_title": project_title,
        "author": author,
        "author_email": author_email,
        "description": args.description,
        "minimum_python_version": minimum_python_version,
    }


def replace_text(
    path: Path,
    replacements: dict[str, str],
    *,
    dry_run: bool,
) -> None:
    """Apply exact string replacements to a file if it exists."""
    if not path.exists():
        return

    content = path.read_text(encoding="utf-8")
    updated = content
    for old, new in replacements.items():
        updated = updated.replace(old, new)

    if updated == content:
        return

    print(f"updated {path}")
    if not dry_run:
        path.write_text(updated, encoding="utf-8")


def update_pyproject(
    path: Path,
    *,
    repository_name: str,
    package_name: str,
    author: str,
    author_email: str,
    description: str,
    minimum_python_version: str,
    dry_run: bool,
) -> None:
    """Update package metadata in pyproject.toml."""
    py_version = python_env_name(minimum_python_version)
    content = path.read_text(encoding="utf-8")
    updated = content
    updated = updated.replace(
        'name = "project_name"',
        f'name = "{repository_name}"',
        1,
    )
    updated = updated.replace(
        'description = "A simple template project."',
        f'description = "{description}"',
        1,
    )
    updated = updated.replace(
        '{ name = "Mario Potato", email = "mario.potato@univr.it" }',
        f'{{ name = "{author}", email = "{author_email}" }}',
        1,
    )
    updated = updated.replace(
        'known-first-party = ["machine_data_model"]',
        'known-first-party = ["project_name"]',
        1,
    )
    updated = updated.replace(
        'known-first-party = ["project_name"]',
        f'known-first-party = ["{package_name}"]',
        1,
    )
    updated = re.sub(
        r'(?m)^requires-python = ">=\d+\.\d+,<4"$',
        f'requires-python = ">={minimum_python_version},<4"',
        updated,
        count=1,
    )
    updated = re.sub(
        r'(?m)^python-version = "\d+\.\d+(?:\.\d+)?"$',
        f'python-version = "{minimum_python_version}.0"',
        updated,
        count=1,
    )
    updated = re.sub(
        r'(?m)^target-version = "py\d{2,3}"$',
        f'target-version = "{py_version}"',
        updated,
        count=1,
    )

    if updated == content:
        return

    print(f"updated {path}")
    if not dry_run:
        path.write_text(updated, encoding="utf-8")


def update_tox(
    path: Path,
    *,
    minimum_python_version: str,
    dry_run: bool,
) -> None:
    """Update tox Python environments from the minimum supported version."""
    if not path.exists():
        return

    tox_env = format_tox_env(versions_from_minimum(minimum_python_version))
    content = path.read_text(encoding="utf-8")
    updated = re.sub(
        r"(?m)^    py(?:\{[\d,]+\}|\d+)$",
        f"    {tox_env}",
        content,
        count=1,
    )

    if updated == content:
        return

    print(f"updated {path}")
    if not dry_run:
        path.write_text(updated, encoding="utf-8")


def update_ci_workflow(
    path: Path,
    *,
    minimum_python_version: str,
    dry_run: bool,
) -> None:
    """Update CI Python matrix and minimum-version-only jobs."""
    if not path.exists():
        return

    versions = versions_from_minimum(minimum_python_version)
    matrix = ", ".join(f"'{version}'" for version in versions)
    content = path.read_text(encoding="utf-8")
    updated = re.sub(
        r"python-version: \[[^\]]+\]",
        f"python-version: [{matrix}]",
        content,
        count=1,
    )
    updated = re.sub(
        r"matrix\.python-version == '\d+\.\d+'",
        f"matrix.python-version == '{minimum_python_version}'",
        updated,
    )

    if updated == content:
        return

    print(f"updated {path}")
    if not dry_run:
        path.write_text(updated, encoding="utf-8")


def update_uv_lock(
    path: Path,
    *,
    minimum_python_version: str,
    dry_run: bool,
) -> None:
    """Update uv lockfile project Python metadata if present."""
    if not path.exists():
        return

    content = path.read_text(encoding="utf-8")
    updated = re.sub(
        r'(?m)^requires-python = ">=\d+\.\d+, <4"$',
        f'requires-python = ">={minimum_python_version}, <4"',
        content,
        count=1,
    )

    if updated == content:
        return

    print(f"updated {path}")
    if not dry_run:
        path.write_text(updated, encoding="utf-8")


def update_docs_index(
    path: Path,
    *,
    project_title: str,
    dry_run: bool,
) -> None:
    """Update the docs landing page heading."""
    content = path.read_text(encoding="utf-8")
    updated = content.replace("# project_name", f"# {project_title}", 1)

    if updated == content:
        return

    print(f"updated {path}")
    if not dry_run:
        path.write_text(updated, encoding="utf-8")


def update_readme(
    path: Path,
    *,
    repository_name: str,
    project_title: str,
    dry_run: bool,
) -> None:
    """Update README title and explicit repository references."""
    content = path.read_text(encoding="utf-8")
    updated = content.replace("# Python Template", f"# {project_title}", 1)
    updated = updated.replace(PLACEHOLDER_REPOSITORY, repository_name)

    if updated == content:
        return

    print(f"updated {path}")
    if not dry_run:
        path.write_text(updated, encoding="utf-8")


def rename_package_dir(package_name: str, *, dry_run: bool) -> None:
    """Rename the placeholder package directory."""
    target_dir = Path(package_name)
    if target_dir == PACKAGE_DIR or not PACKAGE_DIR.exists():
        return

    if target_dir.exists():
        raise FileExistsError(
            f"Cannot rename {PACKAGE_DIR} because {target_dir} already exists."
        )

    print(f"renamed {PACKAGE_DIR} -> {target_dir}")
    if not dry_run:
        PACKAGE_DIR.rename(target_dir)


def main() -> int:
    """Run the template bootstrap process."""
    args = parse_args()
    metadata = resolve_metadata(args)
    repository_name = metadata["repository_name"]
    package_name = metadata["package_name"]
    project_title = metadata["project_title"]
    minimum_python_version = metadata["minimum_python_version"]

    if not repository_name:
        raise ValueError("repository_name must not be empty.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", repository_name):
        raise ValueError(
            "repository_name must contain only letters, numbers, '.', '_' "
            "or '-'."
        )
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", package_name):
        raise ValueError(
            "package_name must be a valid Python package identifier."
        )

    for path in PACKAGE_FILES:
        replace_text(
            path,
            {PLACEHOLDER_PACKAGE: package_name},
            dry_run=args.dry_run,
        )

    for path in REPOSITORY_FILES:
        replace_text(
            path,
            {PLACEHOLDER_REPOSITORY: repository_name},
            dry_run=args.dry_run,
        )

    update_readme(
        Path("README.md"),
        repository_name=repository_name,
        project_title=project_title,
        dry_run=args.dry_run,
    )
    update_docs_index(
        DOCS_INDEX,
        project_title=project_title,
        dry_run=args.dry_run,
    )
    update_pyproject(
        Path("pyproject.toml"),
        repository_name=repository_name,
        package_name=package_name,
        author=metadata["author"],
        author_email=metadata["author_email"],
        description=metadata["description"],
        minimum_python_version=minimum_python_version,
        dry_run=args.dry_run,
    )
    update_tox(
        Path("tox.ini"),
        minimum_python_version=minimum_python_version,
        dry_run=args.dry_run,
    )
    update_ci_workflow(
        Path(".github/workflows/ci.yaml"),
        minimum_python_version=minimum_python_version,
        dry_run=args.dry_run,
    )
    update_uv_lock(
        Path("uv.lock"),
        minimum_python_version=minimum_python_version,
        dry_run=args.dry_run,
    )
    rename_package_dir(package_name, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
