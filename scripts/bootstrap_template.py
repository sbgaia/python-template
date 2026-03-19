#!/usr/bin/env python3
"""Bootstrap a repository created from this template."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PLACEHOLDER_PACKAGE = "project_name"
PLACEHOLDER_REPOSITORY = "python-template"
PLACEHOLDER_AUTHOR = "Mario Potato"
PLACEHOLDER_AUTHOR_EMAIL = "mario.potato@univr.it"
PLACEHOLDER_DESCRIPTION = "A simple template project."

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
        default=Path.cwd().name,
        help="Repository/distribution name, defaults to the current directory.",
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
        "--dry-run",
        action="store_true",
        help="Print the planned changes without modifying files.",
    )
    return parser.parse_args()


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
    dry_run: bool,
) -> None:
    """Update package metadata in pyproject.toml."""
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
    repository_name = args.repository_name.strip()
    package_name = (
        args.package_name or repository_name.replace("-", "_")
    ).strip()
    project_title = (
        args.project_title
        or repository_name.replace("-", " ").replace("_", " ").title()
    ).strip()

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
        author=args.author,
        author_email=args.author_email,
        description=args.description,
        dry_run=args.dry_run,
    )
    rename_package_dir(package_name, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
