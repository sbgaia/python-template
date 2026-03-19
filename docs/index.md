# Python Template

This site is built with MkDocs Material and the API reference is rendered
directly from the Python package and its docstrings.

## Development

Install the development dependencies and run the documentation server locally:

```bash
uv sync --extra dev
uv run mkdocs serve
```

Build the static site with:

```bash
uv run mkdocs build --strict
```

## API reference

The `api.md` page renders the package directly through `mkdocstrings`. Keep
your module, class, and function docstrings up to date and the published API
documentation will follow.
