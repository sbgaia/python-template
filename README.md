# Python Template

This template contains the standard structure for a Python repository for the Glacier project. The template is designed to be used as a starting point for new python projects with support for dockerized development and deployment.

## Bootstrap the template

After creating a new repository from this template, run:

```bash
python scripts/bootstrap_template.py your-repository-name
```

This renames the placeholder package directory, updates the package metadata, and rewrites the main `project_name` and `python-template` references across the repository. Use `--package-name`, `--project-title`, `--author`, `--author-email`, or `--description` if the defaults inferred from the repository name are not enough.

When the repository is created on GitHub from `Use this template`, the
`Bootstrap Template` workflow also runs automatically on the first push and
uses GitHub metadata to rename the repository placeholders. It derives the
repository name from `github.repository`, the author from
`github.repository_owner`, and the author email from the GitHub noreply
address for the triggering actor.

## Getting started

- <code>Use this template > Create a new repository</code> : You can clone this template from the UI by clicking on the upper left repository button.
- <code>Use this template > Open in codespace</code> : Alternatively, you can directly try it out in Github codespace. Codespace is a Github feature that allows you to develop directly in the cloud using VSCode devcontainer. For more information, please refer to <a href="https://docs.github.com/en/codespaces">Github Codespace</a>.
- <code>git clone git@github.com:esd-univr/python-template.git</code> : Or, you can clone this template from the command line.

## Installation

Once the project cloned, you can install the project dependencies.
For development, you can use the `dev` extra to install the development dependencies.

```bash
uv sync --extra dev
```

or using pip:

```bash
pip install -e .[dev]
# install python extension for .env file
pip install python-dotenv
# Note: the .env file must be loaded manually in the main script (https://pypi.org/project/python-dotenv/)
```

This template includes the following software and tools:

- [uv](https://docs.astral.sh/uv/) - A Python package and project manager.
- [Ruff](https://docs.astral.sh/ruff/) - A Python linter and code formatter.
- [MyPy](https://mypy.readthedocs.io/en/stable/) - Static type checker for Python. It ensures that the variables and functions are used correctly.
- [Pytest](https://docs.pytest.org/en/stable/) - Python testing framework. It is used to write and run tests for the project.
- [Tox](https://tox.wiki/en/latest/) - A tool for automating and standardizing testing in Python. It is used to run the tests with multiple Python versions, check the code quality, and build the documentation.
- [Pre-commit](https://pre-commit.com/) - A framework for managing and maintaining multi-language pre-commit hooks. It is used to enforce a consistent code style and quality in each commit.
- [Containers](https://www.docker.com/) - Containers are a standard unit of software that packages up code and all its dependencies into a single `container image`. This, simplifies the deployment process of the application across different computing environments.
- [Devcontainer](https://code.visualstudio.com/docs/devcontainers/containers) - VS Code extension that allows you to use a Docker container as a full-featured development environment.
- [MkDocs](https://www.mkdocs.org/) - Static documentation site generator used to build the project documentation.
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) - The documentation theme used by the template.
- [mkdocstrings](https://mkdocstrings.github.io/) - API reference generator that renders documentation directly from the Python code and its docstrings.
- [GitHub Actions](https://docs.github.com/en/actions) - Automate, customize, and execute your software development workflows in your repository. Actions are used to run the tests, check the code quality, build the documentation, building the library and publish it to packages repositories (e.g. PyPi), and much more.

## Project structure

| Directory       | Status   | Description                                                                                                                                                                                                                                                                                                                                                          |
| --------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.devcontainer` | Optional | Devcontainer configuration directory. It contains a `Dockerfile` used to build the development container, and a `devcontainer.json` file that specifies the container configuration. For more information, please refer to <a href="https://code.visualstudio.com/docs/devcontainers/containers">VS Code Devcontainer</a>.                                           |
| `.github`       | Optional | Github configuration, mainly used to store GitHub actions.                                                                                                                                                                                                                                                                                                           |
| `docs`          | Required | The docs directory contains the MkDocs content for your project. The default configuration uses `mkdocstrings` so the API documentation is rendered directly from the Python package and its docstrings. **Documentation is mandatory for all projects: remember how many times you complained or will complain about the lack of documentation in other projects**. |
| `examples`      | Optional | The examples directory contains all the examples of your project.                                                                                                                                                                                                                                                                                                    |
| `project_name`  | Required | The project_name directory contains all the source code of your project.                                                                                                                                                                                                                                                                                             |
| `resources`     | Optional | Resources are used to store additional files that are used within your project (e.g. configuration files, images, etc.).                                                                                                                                                                                                                                             |
| `scripts`       | Optional | The scripts directory contains all the utility scripts that are useful for the development of your project, such as the build script, the test script, etc.                                                                                                                                                                                                          |
| `tests`         | Required | The tests directory contains all the tests of your project and should follow the same hierarchical structure than the `project_name` directory. If you have a module `project_name/module.py`, you should have a test file `tests/test_module.py`.                                                                                                                   |
| `CHANGELOG.md`  | Optional | The changelog file contains a curated, chronologically ordered list of notable changes for each version of a project.                                                                                                                                                                                                                                                |
