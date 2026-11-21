# Grow.dev

[![PyPI](https://img.shields.io/pypi/v/grow.svg)](https://pypi.org/project/grow/)
[![GitHub Actions][github-image]][github-url]
[![Downloads](https://img.shields.io/github/downloads/grow/grow/total.svg)](https://github.com/grow/grow/releases)

Grow is a declarative tool for rapidly building, launching, and maintaining high-quality static HTML.

- Easy installation
- Jinja template engine
- Content managed in YAML and JSON files
- Data-binding between content and templates
- Configuration-based site architecture
- Easy URL changes
- Flexible internationalization and translation
- Integration with external CMSes
- Integration with Google Sheets
- Fast builds

## Quick start

Install Grow with [uv](https://docs.astral.sh/uv/) or `pip`:

```bash
# Run or install globally with uv:
uv tool install grow

# Or install with pip:
pip install grow
```

Create and run a site using a starter:

```bash
git clone https://github.com/grow/starter
cd starter
grow install
grow run
```

## Documentation

Visit https://grow.dev to read the documentation.

[github-image]: https://github.com/grow/grow/workflows/Test/badge.svg
[github-url]: https://github.com/grow/grow/actions
