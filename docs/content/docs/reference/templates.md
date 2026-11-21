---
$title: Templates
$category: Reference
$order: 1.03
---
# Templates

Grow renders pages using [Jinja2](https://jinja.palletsprojects.com/) templates stored in your pod's `/views/` directory. Grow injects document context variables, a `g` helper namespace, and built-in localization and formatting filters into every template.

## Template globals

These variables are available in every template without a prefix. Avoid shadowing them with `{% set %}`.

| Variable | Type | Description |
|---|---|---|
| `doc` | `Document` | The current document being rendered. See [Documents]([url('/content/docs/reference/documents.md')]). |
| `env` | `Env` | Active build/deployment environment (`name`, `host`, `port`, `scheme`, `fingerprint`). |
| `podspec` | `PodSpec` | Parsed contents of [`podspec.yaml`]([url('/content/docs/reference/podspec.md')]). |
| `_(text)` | Function | Alias for `gettext()` — marks a string for extraction and translates it for `doc.locale`. |
| `gettext(text, **vars)` | Function | Translates a string using the active locale's `.po` catalog. |
| `ngettext(singular, plural, n, **vars)` | Function | Translates a pluralized string based on `n`. |

### `doc`

```jinja
<h1>{{ doc.title }}</h1>
<p class="category">{{ doc.category }}</p>
<article>{{ doc.html | safe }}</article>

{# Access custom YAML front matter and collection blueprint fields #}
<p>{{ doc.author }}</p>
<p>{{ doc.collection.section_title }}</p>
```

### `env`

```jinja
{# Target behavior by environment name (e.g. dev, staging, prod) #}
{% if env.name == 'prod' %}
  <link rel="canonical" href="{{ env.scheme }}://{{ env.host }}{{ doc.url.path }}">
{% endif %}
```

### `podspec`

```jinja
<title>{{ doc.title }} — {{ podspec.title }}</title>
<meta name="author" content="{{ podspec.meta.site_author }}">
```

### `_()`, `gettext()`, and `ngettext()`

```jinja
{# Simple translated string #}
<h1>{{ _('Welcome') }}</h1>

{# Named placeholders #}
<p>{{ _('Hello, %(name)s', name=doc.author) }}</p>

{# Singular / plural forms #}
<p>{{ ngettext('%(num)d article', '%(num)d articles', posts | length, num=posts | length) }}</p>
```


## Helper functions (`g.*`)

All Grow template helpers live under the `g` namespace so they never collide with your front matter variables.

| Function | Returns | Description |
|---|---|---|
| `g.doc(path, locale=None)` | `Document` | Fetches a single document by pod path. |
| `g.docs(collection, ...)` | `list[Document]` | Queries documents in a collection with optional sorting/filtering. |
| `g.categories(collection, ...)` | `list[(str, list[Document])]` | Groups documents in a collection by `$category`. |
| `g.collection(path)` | `Collection` | Returns a single collection object. |
| `g.collections(paths=None)` | `list[Collection]` | Lists all (or specified) collections in the pod. |
| `g.static(path, locale=None)` | `StaticFile` | Resolves a static asset with fingerprinting and build-time existence checks. |
| `g.statics(dir_path, locale=None)` | `list[StaticFile]` | Lists all static files inside a directory. |
| `g.url(path, locale=None)` | `Url` | Returns the resolved `Url` object for a document pod path. |
| `g.yaml(path)` | `dict \| list` | Loads a YAML file (with translation tagging and `?key.subkey` lookup). |
| `g.json(path)` | `dict \| list` | Loads a JSON file by pod path. |
| `g.csv(path, locale=None)` | `list[dict]` | Parses a CSV file into a list of row dicts. |
| `g.date(value, from=...)` | `datetime` | Parses a date string using Python `strptime` directives. |
| `g.locale(code)` | `Locale` | Returns a Babel `Locale` object for a locale code. |
| `g.locales(codes)` | `list[Locale]` | Returns a list of Babel `Locale` objects. |

### `g.doc` and `g.docs`

```jinja
{# Fetch a specific document (optionally in another locale) #}
{% set home = g.doc('/content/pages/index.md') %}
{% set home_fr = g.doc('/content/pages/index.md', locale='fr') %}

{# List documents in a collection sorted by multiple fields #}
<ul>
  {% for post in g.docs('blog', order_by=('dates.published', 'title'), reverse=True) %}
    <li><a href="{{ post.url.path }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>
```

### `g.categories`

Groups documents in a collection by their `$category` front matter field:

```jinja
{% for category, items in g.categories('docs') %}
  <h3>{{ category }}</h3>
  <ul>
    {% for item in items %}
      <li><a href="{{ item.url.path }}">{{ item.title }}</a></li>
    {% endfor %}
  </ul>
{% endfor %}
```

### `g.collection` and `g.collections`

```jinja
{% set pages = g.collection('pages') %}
{% for col in g.collections(['docs', 'blog']) %}
  <h2>{{ col.title }}</h2>
{% endfor %}
```

### `g.static` and `g.statics`

Always reference static assets with `g.static()` rather than hardcoding URLs. Grow rewrites fingerprinted filenames automatically and fails the build if a referenced asset is missing.

Requires a matching entry in `static_dirs` in `podspec.yaml`.

```jinja
<link rel="stylesheet" href="{{ g.static('/static/css/main.css').url.path }}">
<img src="{{ g.static('/static/images/hero.png', locale=doc.locale).url.path }}" alt="">

{# List every image in a static directory #}
{% for asset in g.statics('/static/gallery/') %}
  <img src="{{ asset.url.path }}" alt="">
{% endfor %}
```

### `g.url`

Returns the `Url` object for a document without loading its body:

```jinja
<a href="{{ g.url('/content/pages/about.md').path }}">About</a>
```

### `g.yaml`, `g.json`, and `g.csv`

Load structured data files directly inside templates:

```jinja
{% set nav = g.yaml('/content/data/nav.yaml') %}
{% set config = g.json('/content/data/config.json') %}
{% set team = g.csv('/content/data/team.csv') %}

<ul>
  {% for member in team %}
    <li>{{ member.name }} — {{ member.role }}</li>
  {% endfor %}
</ul>
```

### `g.date`

Parses a string into a Python `datetime` using [Python `strptime` directives](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior):

```jinja
{% set release = g.date('2026-11-21', from='%Y-%m-%d') %}
<time>{{ release | date(format='long') }}</time>
```

### `g.locale` and `g.locales`

Convert locale codes into [Babel `Locale`](https://babel.pocoo.org/en/latest/api/core.html#babel.core.Locale) objects:

```jinja
{% set current = g.locale('fr_CA') %}
{{ current.display_name }}

{% for loc in g.locales(['en', 'fr', 'ja']) %}
  <span>{{ loc.get_display_name(loc) }}</span>
{% endfor %}
```


## Built-in filters

Grow includes 17 built-in Jinja2 filters for formatting, localization, URLs, and template rendering.

| Filter | Example | Description |
|---|---|---|
| `currency` | `{{ 123.45 \| currency('USD') }}` | Localized currency formatting via [Babel](https://babel.pocoo.org/en/latest/api/numbers.html#babel.numbers.format_currency). |
| `date` | `{{ dt \| date(format='medium') }}` | Localized date formatting via [Babel](https://babel.pocoo.org/en/latest/api/dates.html#babel.dates.format_date). |
| `datetime` | `{{ dt \| datetime(format='short') }}` | Localized datetime formatting via Babel. |
| `time` | `{{ dt \| time(format='short') }}` | Localized time formatting via Babel. |
| `decimal` | `{{ 1234.56 \| decimal }}` | Localized decimal formatting via Babel. |
| `number` | `{{ 12345 \| number }}` | Localized integer/number formatting via Babel. |
| `percent` | `{{ 0.25 \| percent }}` | Localized percentage formatting via Babel. |
| `deeptrans` | `{{ data \| deeptrans }}` | Recursively translates all strings in a dict or list via `gettext`. |
| `expand_partial` | `{{ 'hero' \| expand_partial }}` | Resolves a partial name to its template path (e.g. `/partials/hero/hero.html`). |
| `hash` | `{{ value \| hash('sha256') }}` | Hashes a string (`sha` / `sha1`, `md5`, `sha256`, `sha512`). |
| `jsonify` | `{{ obj \| jsonify }}` | Serializes a Python object to JSON. |
| `markdown` | `{{ text \| markdown \| safe }}` | Renders a Markdown string to HTML. |
| `relative` | `{{ target.url.path \| relative }}` | Converts an absolute path to a path relative to the current `doc.url.path`. |
| `re_replace` | `{{ text \| re_replace('\s+', '-') }}` | Replaces regex matches in a string. |
| `render` | `{{ doc.html \| render \| safe }}` | Evaluates Jinja2 syntax inside a string using the current template context. |
| `shuffle` | `{{ items \| shuffle }}` | Returns a randomly shuffled copy of a list. |
| `slug` | `{{ 'Hello World!' \| slug }}` | Converts text to a URL-friendly slug (`hello-world`). |

### Formatting & localization examples

```jinja
{{ 1234.50 | currency('EUR', locale='de_DE') }}
{{ doc.date | date(format='long', locale='ja_JP') }}
{{ 0.875 | percent }}
```

### Markdown, rendering, and data examples

```jinja
{# Render a Markdown field from YAML front matter #}
{{ doc.summary | markdown | safe }}

{# Evaluate Jinja expressions inside document HTML #}
{{ doc.html | render | safe }}

{# Embed structured data safely for client-side scripts #}
<script type="application/json" id="page-data">
  {{ doc.metadata | jsonify | safe }}
</script>

{# Compute a relative link from the current page #}
<a href="{{ g.doc('/content/pages/about.md').url.path | relative }}">About</a>
```
