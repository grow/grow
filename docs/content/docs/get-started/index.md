---
$category: Get started
$order: 0
$path: /
$title: Introduction
$titles:
  nav: Docs
  side: Welcome
---
# A declarative, file-based static site generator

Grow is a simple, declarative static site generator written in Python. Author your content in YAML, JSON, and Markdown, bind it to [Jinja2](https://jinja.palletsprojects.com/) templates, and compile to fast, self-contained static HTML with built-in localization.

Grow keeps content strictly separate from presentation and makes zero assumptions about your frontend CSS or JavaScript stack.

## Quick start

Install Grow with [uv](https://docs.astral.sh/uv/) (Python 3.9 – 3.12):

```bash
uv tool install grow
```

Clone the monorepo and preview the zero-Node starter pod locally:

```bash
git clone https://github.com/grow/grow.git
cd grow
grow run examples/starter
```

Build the static site to `build/`:

```bash
grow build examples/starter
```

## Key features

- **Declarative content & routing**: Define collections, URL patterns, and metadata in YAML — update URLs without breaking internal links.
- **Jinja2 templates & partials**: Compose reusable HTML templates and modular page partials with full template-level link validation.
- **Built-in internationalization (i18n)**: Mark translatable strings in YAML and templates, manage standard `.po` message catalogs, and localize URLs and content per locale.
- **Environment-aware builds**: Target development, staging, and production configurations from a single `podspec.yaml`.
- **Zero frontend lock-in**: Bring plain CSS/JS or any external bundler you prefer.
- **Static output everywhere**: Deploy `build/` to GitHub Pages, Cloudflare Pages, Netlify, Cloud Storage, S3, or any static host.

## Next steps

- [Install Grow]([url('/content/docs/get-started/install.md')]) — `uv`, `pip`, and Docker setup.
- [Workflow: Developing & building]([url('/content/docs/workflow/building.md')]) — Local server, Dev Console (`/_grow`), and production builds.
- [Starter project on GitHub](https://github.com/grow/grow/tree/main/examples/starter) — Minimal localized pod with zero Node dependencies.

<a href="/codelab/" class="button button--lg button--icon-end">
  Walk through the codelab &rarr;
</a>
