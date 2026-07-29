# Python Template

<!-- coverage:start -->

![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)

Current coverage: **100.00%**. Required minimum: **90.00%**.

Coverage details: 30/30 statements and 6/6 branches covered.
CI updates this block from `coverage.xml` after the coverage workflow runs.

<!-- coverage:end -->

This repository is a Python project template for the Glacier project. It gives
new projects a working package layout, uv-based dependency management, tests,
Ruff formatting and linting, Pyrefly type checking, Sphinx documentation,
Docker support, and GitHub Actions workflows.

## Create a project from the template

Create a new repository with GitHub's **Use this template** button. The
`Bootstrap Template` workflow attempts to rewrite the template placeholders on
the first run and commit the result back to the new repository.

If the workflow does not run in your GitHub environment, run the bootstrap
script manually:

```bash
python scripts/bootstrap_template.py your-repository-name
```

The bootstrap script:

- renames the source package directory
- updates package metadata in `pyproject.toml`
- rewrites imports and tool configuration from the template package name
- updates README and documentation titles
- adjusts the supported Python versions in tox and CI when requested

Use explicit options when the defaults inferred from the repository name are not
enough:

```bash
python scripts/bootstrap_template.py your-repository-name \
  --package-name your_package \
  --project-title "Your Project" \
  --author "Your Name" \
  --author-email "you@example.com" \
  --description "Short project description." \
  --minimum-python-version 3.12
```

Repository names may contain dashes. The default Python package name is the
repository name with dashes converted to underscores.

## Install dependencies

Install the project for development:

```bash
uv sync --extra dev --extra docs
```

Install only runtime dependencies:

```bash
uv sync
```

Using pip is also supported:

```bash
pip install -e .[dev,docs]
```

## Run checks

Run tests for the active Python environment:

```bash
uv run pytest
```

Run type checks:

```bash
uv run tox -e type
```

Run coverage with the configured threshold:

```bash
uv run tox -e coverage
```

The `Coverage` workflow updates the README badge and summary from `coverage.xml` on pushes to `main` and `dev`.

Audit dependencies for known vulnerabilities:

```bash
uv run tox -e security
```

Run Ruff fixes and formatting:

```bash
uv run tox -e formatter
```

Build and smoke-test the package artifacts:

```bash
uv run tox -e build
```

Preview the generated changelog:

```bash
uv run tox -e changelog
```

Build the documentation:

```bash
uv run tox -e docs
```

Build and smoke-test the Docker image:

```bash
docker build --pull -t python-template:ci .
docker run --rm python-template:ci uv run python -c "import project_name"
```

See `CONTRIBUTING.md` for the full local verification workflow and the
generated-project smoke test.

## Documentation

Documentation lives in `docs/` and is built with Sphinx. Manual pages are
written in Markdown with MyST, while API reference pages are generated from
Google-style Python docstrings.

The canonical documentation build is:

```bash
uv run tox -e docs
```

This runs Sphinx with warnings treated as errors and writes HTML to
`docs/_build/html`. Use a live preview while editing docs:

```bash
uv run sphinx-autobuild docs docs/_build/html
```

The live preview is for authoring convenience; `tox -e docs` is the build that
must pass before merging. Read the Docs builds the site from
`.readthedocs.yaml`, and GitHub Actions uploads the built HTML as an artifact on
pull requests.

## Project structure

| Path            | Status   | Purpose                                                                   |
| --------------- | -------- | ------------------------------------------------------------------------- |
| `.github/`      | Optional | GitHub Actions, Dependabot, and repository guidance.                      |
| `docs/`         | Required | Sphinx documentation, including manual pages and generated API reference. |
| `examples/`     | Optional | Runnable examples for users and contributors.                             |
| `project_name/` | Required | Source package. The bootstrap script renames this directory.              |
| `scripts/`      | Optional | Repository automation scripts, including the bootstrap script.            |
| `tests/`        | Required | Pytest test suite. Mirror the package structure where practical.          |
| `Dockerfile`    | Optional | Container build for running the project example.                          |
| `cliff.toml`    | Optional | git-cliff changelog generation rules.                                     |
| `tox.ini`       | Required | Local and CI task definitions.                                            |

## Included tools

- [uv](https://docs.astral.sh/uv/) for dependency management
- [Tox](https://tox.wiki/en/latest/) for repeatable test and build tasks
- [Pytest](https://docs.pytest.org/en/stable/) for tests
- [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
- [Pyrefly](https://pyrefly.org/) for static type checking
- [Sphinx](https://www.sphinx-doc.org/) for documentation generation
- [MyST Parser](https://myst-parser.readthedocs.io/) for Markdown in Sphinx
- [Read the Docs](https://readthedocs.org/) for hosted documentation
- [pip-audit](https://pypi.org/project/pip-audit/) for dependency vulnerability checks
- [git-cliff](https://git-cliff.org/) for changelog generation
- [GitHub Actions](https://docs.github.com/en/actions) for CI automation
