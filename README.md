# Grow

[![PyPI](https://img.shields.io/pypi/v/grow.svg)](https://pypi.org/project/grow/)
[![Python](https://img.shields.io/pypi/pyversions/grow.svg)](https://pypi.org/project/grow/)
[![Test](https://github.com/grow/grow/actions/workflows/test.yml/badge.svg)](https://github.com/grow/grow/actions/workflows/test.yml)
[![Lint](https://github.com/grow/grow/actions/workflows/lint.yml/badge.svg)](https://github.com/grow/grow/actions/workflows/lint.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Grow** is a declarative, file-based static site generator for rapid, high-quality web site production.

## Key Features

- **Data-driven content**: Author content in YAML, JSON, and Markdown—keeping content cleanly separated from presentation.
- **Jinja2 templates**: Bind structured content collections to reusable HTML templates and partials.
- **Declarative routing & URLs**: Configure URL structures in YAML and reference pages/assets with template tags so URL changes never break links.
- **Built-in internationalization (i18n)**: Tag strings for translation, manage PO message catalogs, and localize content site-wide or per document.
- **Integrations**: Pull content from Google Drive/Docs/Sheets and Blogger, or sync translations with Google Sheets.
- **Deploy anywhere**: Build to a self-contained static fileset or deploy directly via built-in targets (local, Git, WebReview, and custom extensions).

## Requirements

- Python **3.9 – 3.12**

## Installation

Install Grow with [uv](https://docs.astral.sh/uv/) or `pip`:

```bash
# Install globally as a CLI tool with uv (recommended)
uv tool install grow

# Or install with pip
pip install grow
```

## Quick Start

Clone a Grow project (such as [grow.dev](https://github.com/grow/grow.dev)), install its dependencies, and start the local development server:

```bash
git clone https://github.com/grow/grow.dev
cd grow.dev
grow install
grow run
```

### Common Commands

```bash
grow run                     # Start the local development server
grow build                   # Build the static site to ./build/
grow deploy <destination>    # Deploy to a configured destination in podspec.yaml
grow translations extract    # Extract translatable strings to message catalogs
grow --help                  # Show all available commands
```

## Docker

Prebuilt images containing Grow, Python, Node.js, Yarn, and Google Cloud CLI are published to Docker Hub and GitHub Container Registry:

```bash
docker run --rm -it -v "$PWD":/site -w /site grow/base grow build
```

## Development

Grow uses `uv`, `pytest`, and `ruff` for local development:

```bash
git clone https://github.com/grow/grow.git
cd grow
uv sync
uv run pytest
uv run ruff check grow/ install.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contributor guide.

## Documentation & License

- Documentation: https://grow.dev
- Source code: https://github.com/grow/grow
- License: [MIT](LICENSE)
