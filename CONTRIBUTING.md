# Contributing to Grow

Thanks for contributing to Grow!

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (manages the Python virtual environment and lockfile)
- Python **3.10 – 3.12**
- Node.js & Yarn (only needed if working on `grow/ui` assets)

## Local Setup

```bash
git clone https://github.com/grow/grow.git
cd grow
uv sync
```

Run the CLI directly from your workspace:

```bash
uv run grow --help
# Or via the wrapper script:
./scripts/grow --help
```

## Testing

Run the full test suite:

```bash
uv run pytest
```

Run a single test file or test case:

```bash
uv run pytest grow/pods/pods_test.py
uv run pytest -k test_read_file
```

Run with coverage:

```bash
uv run pytest --cov=grow --cov-report=term-missing
```

## Linting & Formatting

Grow uses [Ruff](https://docs.astral.sh/ruff/) for linting and code formatting (configured in `pyproject.toml`):

```bash
uv run ruff check grow/ install.py
uv run ruff format --check grow/ install.py
```

To auto-fix lint issues and format your changes:

```bash
uv run ruff check --fix grow/ install.py
uv run ruff format grow/ install.py
```

## Building UI Assets

To build the admin and UI static bundles (used by `test_admin`/`test_ui` and package releases):

```bash
yarn --cwd grow/ui install
yarn --cwd grow/ui build
```

## Building Packages & Docker Images

Build sdist and wheel distributions:

```bash
uv build
```

Build and push Docker images (see `docker_push.sh`):

```bash
./docker_push.sh        # Push to Docker Hub
./docker_push.sh gcr.io # Push to GCR
./docker_push.sh all    # Push to both
```

## Commit Messages & Releases

[Release Please](https://github.com/googleapis/release-please) automates changelogs, version bumps, and PyPI/Docker releases based on commit history:

- Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) (e.g., `fix:`, `feat:`, `perf:`, `refactor:`, `docs:`, `chore:`, `build:`).
- Follow the [Angular commit convention](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#type) for commit types.
