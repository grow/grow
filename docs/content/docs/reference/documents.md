---
$title: Documents
$category: Reference
$order: 1.05
---
# Documents

All content in Grow lives in **documents** inside `/content/<collection>/`. Every file in a collection directory (other than `_blueprint.yaml`) is treated as a document.

Documents with a resolved `$path` and `$view` (either set directly or inherited from `_blueprint.yaml`) are rendered as pages. Documents without a `$path` act as reusable data or partial documents.

## Supported file formats

| Extension | Format | Front matter | `doc.html` / `doc.body` |
|---|---|---|---|
| `.md`, `.markdown`, `.mdown`, `.mkd` | Markdown | Optional (`---` delimited) | Rendered HTML / raw Markdown |
| `.yaml`, `.yml` | YAML | Whole file is front matter | `None` |
| `.html`, `.htm` | HTML | Optional (`---` delimited) | Raw HTML source |

### Markdown document

```markdown
​---
$title: Hello, Grow
$category: Guides
author: Ada Lovelace
​---
# Welcome

Write standard **Markdown** in the body and access metadata via `{{ doc.author }}`.
```

### YAML document

```yaml
# /content/pages/home.yaml
$title: Home
$view: /views/home.html
$path: /

hero:
  heading@: Build fast static sites
  cta_url: !g.url /content/pages/about.md
```

### HTML document

```jinja
​---
$title: Custom landing page
$view: /views/base.html
items:
  - One
  - Two
​---
<ul>
  {% for item in doc.items %}
    <li>{{ item }}</li>
  {% endfor %}
</ul>
```

In your base view, evaluate Jinja inside an HTML document's body using `{{ doc.html | render | safe }}`.


## YAML constructors

Use custom YAML tags in front matter or data files to reference other pod files, URLs, static assets, and translatable strings:

| Constructor | Example | Description |
|---|---|---|
| `!_` | `!_ Hello world` | Marks an inline string value for translation. |
| `!g.doc` | `!g.doc /content/pages/about.md` | Loads another `Document` object. |
| `!g.url` | `!g.url /content/pages/about.md` | Resolves to a document's `Url` object. |
| `!g.static` | `!g.static /static/images/logo.svg` | Resolves to a `StaticFile` object. |
| `!g.yaml` | `!g.yaml /content/data/nav.yaml` | Loads a YAML file (supports `?key.subkey`). |
| `!g.json` | `!g.json /content/data/config.json` | Loads a JSON file (supports `?key.subkey`). |
| `!g.csv` | `!g.csv /content/data/team.csv` | Loads a CSV file as a list of dicts. |
| `!g.string` | `!g.string products.categories.art` | References a key in `/content/strings/<file>.yaml`. |

### Deep key lookups

Append `?key.sub_key` to `!g.yaml` or `!g.json` to extract a nested value:

```yaml
nav_items: !g.yaml /content/data/site.yaml?navigation.primary
api_url: !g.json /content/data/config.json?endpoints.public
```

### String references (`!g.string`)

Store shared strings in `/content/strings/<name>.yaml` and reference them as `<name>.<key>.<subkey>`:

```yaml
# /content/strings/products.yaml
categories:
  art@: Art
  tech@: Technology
```

```yaml
# /content/pages/art.yaml
category_label: !g.string products.categories.art
```


## Document API (properties & methods)

Every document exposes built-in properties and helper methods inside templates.

### Properties

| Property | Type | Description |
|---|---|---|
| `doc.title` | `str` | Canonical title from `$title`. |
| `doc.url` | `Url` | Resolved URL (`url.path`, `url.host`, `url.scheme`, `url.port`). |
| `doc.html` | `str \| None` | Rendered HTML (for `.md`) or raw HTML (for `.html`). Pipe to `\| safe`. |
| `doc.body` | `str \| None` | Unprocessed body text after front matter. |
| `doc.fields` | `dict` | All parsed front matter fields. |
| `doc.pod_path` | `str` | Full path in the pod (e.g. `/content/pages/about.md`). |
| `doc.base` | `str` | Filename without extension (e.g. `about`). |
| `doc.slug` | `str` | Slug from `$slug` or slugified `$title`. |
| `doc.collection` | `Collection` | Parent `Collection` object. |
| `doc.collection_base` | `str` | Subdirectory relative to the collection (e.g. `/` or `/sub/`). |
| `doc.collection_path` | `str` | File path relative to the collection (e.g. `/sub/about.md`). |
| `doc.category` | `str \| None` | Category from `$category`. |
| `doc.date` | `datetime \| None` | Date from `$date`. |
| `doc.order` | `int \| float \| None` | Sort order from `$order`. |
| `doc.hidden` | `bool` | Whether `$hidden: true` is set. |
| `doc.parent` | `Document \| None` | Parent document from `$parent`. |
| `doc.view` | `str \| None` | Template pod path from `$view` or blueprint. |
| `doc.path_format` | `str \| None` | URL path format; falsy if the document does not generate a route. |
| `doc.exists` | `bool` | Whether the underlying file exists in the pod. |
| `doc.locale` | `Locale` | Current Babel `Locale` (e.g. `doc.locale.is_rtl`, `doc.locale.get_display_name('en')`). |
| `doc.locales` | `list[Locale]` | All locales this document is available in. |
| `doc.default_locale` | `Locale` | Document's default fallback locale. |
| `doc.hreflang` | `str` | BCP-47 language tag suitable for `<link rel="alternate" hreflang="...">`. |
| `doc.footnotes` | `Footnotes` | Footnote manager for registering and rendering page footnotes. |
| `doc.sitemap` | `dict` | Sitemap metadata from `$sitemap`. |

### Methods

#### `doc.titles(name=None)`

Returns a context-specific title from `$titles`, falling back to `$title`:

```yaml
$title: Getting Started with Grow
$titles:
  nav: Get started
  breadcrumb: Start
```

```jinja
{{ doc.titles('nav') }}         {# Get started #}
{{ doc.titles('breadcrumb') }}  {# Start #}
{{ doc.titles('unknown') }}     {# Getting Started with Grow #}
{{ doc.title }}                 {# Getting Started with Grow #}
```

#### `doc.dates(name=None)`

Returns a named date from `$dates`:

```yaml
$dates:
  created: 2026-01-15
  published: 2026-11-21
```

```jinja
{{ doc.dates('published') | date(format='long') }}
```

#### `doc.localize(locale)`

Returns the same document localized to a different locale (useful for language switchers and `hreflang` tags):

```jinja
{% for loc in doc.locales %}
  {% set alt = doc.localize(loc) %}
  <link rel="alternate" hreflang="{{ alt.hreflang }}" href="{{ alt.url }}">
{% endfor %}
```

#### `doc.prev(docs=None)` and `doc.next(docs=None)`

Returns the previous or next document in the collection's default order (or within an explicit list of documents), or `None` at the ends:

```jinja
{% set prev_doc = doc.prev() %}
{% set next_doc = doc.next() %}

{% if prev_doc %}
  <a href="{{ prev_doc.url.path }}">{{ prev_doc.title }}</a>
{% endif %}
{% if next_doc %}
  <a href="{{ next_doc.url.path }}">{{ next_doc.title }}</a>
{% endif %}
```

### Checking whether a document builds a URL

Before linking to arbitrary documents in a collection, check `item.path_format` to skip non-routed partial/data documents:

```jinja
{% for item in g.docs('pages') if item.path_format %}
  <a href="{{ item.url.path }}">{{ item.title }}</a>
{% endfor %}
```

### Working with `doc.locale`

```jinja
<html lang="{{ doc.hreflang }}" dir="{{ 'rtl' if doc.locale.is_rtl else 'ltr' }}">

{# Language name in its own language and in English #}
{{ doc.locale.get_display_name(doc.locale) }}
{{ doc.locale.get_display_name('en') }}
```

### Working with `doc.footnotes`

```jinja
{# Register a footnote inline #}
{% set symbol = doc.footnotes.add('See the podspec reference for details.') %}
<span>Important note<a href="#footnote-{{ doc.footnotes.index(symbol) }}">{{ symbol }}</a></span>

{# Render collected footnotes at the bottom of the page #}
{% for symbol, text in doc.footnotes %}
  <p id="footnote-{{ loop.index0 }}">{{ symbol }} {{ _(text) }}</p>
{% endfor %}
```


## Built-in front matter fields (`$*`)

Fields prefixed with `$` control Grow's built-in behavior. Omit the `$` when reading them in templates (for example, `$title` is read as `doc.title`).

| Field | Example | Description |
|---|---|---|
| `$title` | `$title: About us` | Canonical document title. |
| `$titles` | `$titles: { nav: About }` | Named alternate titles accessed via `doc.titles('nav')`. |
| `$path` | `$path: /about/` | Overrides the collection blueprint's serving URL path (use `~` to disable routing). |
| `$view` | `$view: /views/page.html` | Overrides the Jinja2 template used to render the document. |
| `$category` | `$category: Guides` | Groups documents for `g.categories()`. |
| `$order` | `$order: 2.5` | Numeric sort order (supports negative and decimal values). |
| `$date` | `$date: 2026-11-21` | Primary document date. |
| `$dates` | `$dates: { updated: 2026-11-21 }` | Named dates accessed via `doc.dates('updated')`. |
| `$slug` | `$slug: custom-slug` | Overrides the auto-generated slug. |
| `$hidden` | `$hidden: true` | Omits the document from `g.docs()` results while still rendering its route. |
| `$parent` | `$parent: /content/pages/index.md` | Declares a parent document for hierarchical navigation. |
| `$localization` | `$localization: { locales: [en, fr] }` | Overrides collection-level localization paths or locales for this document. |
| `$sitemap` | `$sitemap: { enabled: false }` | Controls inclusion in generated `sitemap.xml`. |
