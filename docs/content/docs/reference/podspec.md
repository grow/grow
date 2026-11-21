---
$title: Podspec
$category: Reference
$order: 1.02
---
# Podspec (`podspec.yaml`)

Every Grow pod has a root `podspec.yaml` file that declares site-wide settings: locales, static asset directories, Markdown extensions, sitemaps, preprocessors, and deployments.

## Complete example

```yaml
# podspec.yaml
grow_version: ">=2.0.0"
title@: My Site
description@: A fast, localized static site.
home: /content/pages/index.md
root: "/"

meta:
  site_author: Example Team

static_dirs:
  - static_dir: /static/
    serve_at: /static/
    fingerprinted: true

localization:
  default_locale: en
  locales:
    - en
    - fr
    - de
  aliases:
    en_uk: en_GB
  require_translations: false
  require_translations@env.prod: true

markdown:
  extensions:
    - kind: markdown.extensions.codehilite
      theme: github-dark

sitemap:
  enabled: true
  path: /sitemap.xml

deployments:
  prod:
    destination: local
    out_dir: ./build/
    env:
      name: prod
      host: example.com
      port: 443
      scheme: https
```


## Core fields

| Field | Description |
|---|---|
| `grow_version` | Optional semver constraint checked by Grow (e.g. `">=2.0.0"`). |
| `title` / `description` | Site-wide title and description, exposed as `podspec.title` / `podspec.description`. |
| `home` | Pod path to the homepage document (accessible as `podspec.home`). |
| `root` | URL root prefix for all routes (defaults to `"/"`). |
| `meta` | Arbitrary site-wide key/value metadata exposed as `podspec.meta`. |


## `static_dirs`

Maps directories in your pod to serving URL prefixes.

```yaml
static_dirs:
  # Serve /static/ files at /static/ with content-hash fingerprints.
  - static_dir: /static/
    serve_at: /static/
    fingerprinted: true

  # Serve /public/ files at the site root (e.g. robots.txt, favicon.ico).
  - static_dir: /public/
    serve_at: /
```

### Fingerprinting

When `fingerprinted: true` is enabled, `/static/css/main.css` is served as `/static/css/main-<hash>.css` for immutable browser caching. Reference fingerprinted files in templates with `{{ g.static('/static/css/main.css').url.path }}`.

### Path filtering (`filter`)

By default, Grow ignores dotfiles (files starting with `.`). Override this globally or per `static_dirs` entry using regex patterns:

```yaml
filter:
  ignore_paths:
    - \.DS_Store$
  include_paths:
    - \.well-known/
```


## `localization`

Configures site-wide locales, aliases, translation enforcement, and locale groups.

```yaml
localization:
  default_locale: en
  locales:
    - en
    - fr
    - de
  aliases:
    en_uk: en_GB
  import_as:
    en_uk:
      - en_GB
  require_translations: false
  require_translations@env.prod: true
  groups:
    europe:
      - de
      - fr
```

- **`default_locale`**: Fallback locale when none is specified on a document or collection.
- **`locales`**: List of locale identifiers generated for the site.
- **`aliases`**: Maps URL/server locale slugs to Grow locale identifiers.
- **`import_as`**: Maps external translation-provider locale codes to internal Grow locales during `grow translations import`.
- **`require_translations`**: Fails builds if untranslated strings remain (can be scoped per environment with `@env.<name>`).
- **`groups`**: Named locale groups usable in YAML front matter (e.g. `headline@locale.europe: ...`).


## `markdown`

Configures Python-Markdown extensions and syntax highlighting themes (via Pygments):

```yaml
markdown:
  extensions:
    - kind: markdown.extensions.codehilite
      theme: github-dark
      classes: false
    - kind: toc
      permalink: false
```

Set `classes: true` to emit CSS classes instead of inline Pygments styles.


## `sitemap`

Automatically generates a `sitemap.xml` covering your site's localized routes:

```yaml
sitemap:
  enabled: true
  path: /{root}/sitemap.xml
  collections:
    - pages
  locales:
    - en
    - fr
```


## `preprocessors` and `extensions`

Configure [preprocessors]([url('/content/docs/reference/preprocessors.md')]) and [Python extensions]([url('/content/docs/extensions/install.md')]) loaded by your pod:

```yaml
preprocessors:
  - kind: google_sheets
    name: strings
    autorun: false
    id: <spreadsheet-id>
    path: /content/data/strings.yaml

extensions:
  jinja2:
    - ext.my_filters.MyFiltersExtension
```


## `deployments`

Defines named targets for `grow deploy <name>` and per-environment `{{ env }}` values. See [Deployment]([url('/content/docs/workflow/deployment.md')]) for full details.

```yaml
deployments:
  prod:
    destination: local
    out_dir: ./build/
    env:
      name: prod
      host: example.com
      port: 443
      scheme: https
```


## `footnotes`

Customizes footnote symbols and numeric-footnote locale rules used by `doc.footnotes`:

```yaml
footnotes:
  numeric_locales_pattern: (US|CA)$
  use_numeric_symbols: false
  symbols:
    - "*"
    - "†"
    - "‡"
    - "§"
```
