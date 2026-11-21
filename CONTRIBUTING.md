# Contributing to Grow

## Development

Grow uses [uv](https://docs.astral.sh/uv/) for Python environment and dependency management, `pytest` for testing, and `ruff` for linting.

```bash
git clone git@github.com:grow/grow.git
cd grow
uv sync
```

Run Grow from the workspace:

```bash
uv run grow --help
```

## Testing & Linting

Run the test suite:

```bash
uv run pytest
```

Run with coverage:

```bash
uv run pytest --cov=grow
```

Run the linter:

```bash
uv run ruff check grow/
```

## Building UI Assets

To build the admin/UI static assets (required for UI server tests and releases):

```bash
yarn --cwd grow/ui install
yarn --cwd grow/ui build
```

## Commit messages

[Release Please](https://github.com/googleapis/release-please) is used to
automatically create changelogs, releases, and versions.

- Commit messages must follow the [Conventional
  Commit](https://www.conventionalcommits.org/en/v1.0.0/) specification
- Follow the [Angular
  convention](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#type)
  to see all commit types

## Docker

- Run `./docker_push.sh` to update docker images.
