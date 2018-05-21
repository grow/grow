---
$title: Templates
$category: Reference
$order: 1.03
---
[TOC]

Grow templates are stored in a pod's `/views/` directory. Templates are processed using the [Jinja2](http://jinja.pocoo.org/docs/) template language. Grow extends Jinja2 with a few variables and functions that make building content-rich web sites more convenient.

Variables have no prefix and are part of the global template scope. Functions are prefixed into the `g` namespace, for example: `g.<function name>`.

## Variables

There are several built-in global variables available to templates. Because these variables are not namespaced, take caution not to overwrite their values.

### doc

The current content document associated with the current page that's being rendered. See the [full documentation for the document API]([url('/content/docs/documents.md')]).

```jinja
{{doc.category}}      # Document's category
{{doc.title}}         # Document's canonical title.
{{doc.titles('nav')}} # Document's "nav" title.
{{doc.html|safe}}     # Document's rendered Markdown body.
{{doc.foo}}           # Value of the "foo" custom field from the YAML front matter.
```

### env

The rendering environment that exists when the page is being built or served.

```jinja
{{env.host}}
{{env.name}}
{{env.port}}
{{env.scheme}}
{{env.fingerprint}}
```

### podspec

Refers to the [`podspec.yaml` configuration file]([url('/content/docs/podspec.md')]) and allows you to access pod-wide settings in templates.

```jinja
{{podspec.title}}         # Pod's title.
{{podspec.project_id}}    # Pod's project ID.
```

## Functions

### _

`_(<string>)`

The `_` tag is a special function used to tag strings in templates for both translation and message extraction.

```jinja
# Simple translation.
{{_('Hello')}}

# A translation with a placeholder.
{{_('Hello, %(name)s', name='Alice')}}
```

### g.categories

`g.categories(<collection>)`

Lists content documents within a collection and groups them by their *$category*. Useful for generating navigation and categorized lists of documents.

```jinja
{% for category, docs in g.categories('pages') %}
  <h3>{{category}}</h3>
  <ul>
    {% for doc in docs %}
      <li>{{doc.title()}}
    {% endfor %}
  </ul>
{% endfor %}
```

### g.collection

`g.collection(<collection>)`

Returns a `Collection` object, given a collection path.

### g.collections

`g.collections(<optional list of collections>)`

Returns a list of all `Collection` objects in the pod, or lists `Collection` objects given a list of collection paths.

```jinja
{{g.collections()}}
{{g.collections(['pages'])}}
```

### g.csv

`g.csv(<path to csv>, locale=<identifier>)`

Parses a CSV file and returns a list of dictionaries mapping header rows to values for each row. Optionally use keyword arguments to filter results. This can be particularly useful for using a spreadsheet for localization (where rows represent values for different locales).

```jinja
{% set people = g.csv('/data/people.csv') %}
{% for person in people %}
  <li>{{person.name}}
{% endfor %}
```

### g.date

`g.date(<DateTime|string>, from=<string>)`

Parses a string into a Date object. Uses [Python date formatting directives](https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior).

```jinja
# Returns a DateTime given a string and a format.
{{g.date('12/31/2000', from='%m/%d/%Y')}}
```

### g.doc

`g.doc(<document path>, locale=<locale>)`

Gets a single content document, given its pod path.

```jinja
{% set foo = g.doc('/content/pages/index.html') %}
{{foo}}

# Returns the fr version of a document.
{{g.doc('/content/pages/index.html', locale='fr')}}
```

### g.docs

`g.docs(<collection>, order_by=<field name>, locale=<locale>)`

Searches content documents within a collection.

```jinja
<ul>
  {% for doc in g.docs('pages') %}
    <li>{{doc.title}}
  {% endfor %}
</ul>
```

The documents can also be sorted by multiple fields.

```jinja
<ul>
  {% for doc in g.docs('pages', order_by=('dates.published', 'title')) %}
    <li>{{doc.title}}
  {% endfor %}
</ul>
```

### g.json

`g.json(<path to json file>)`

Returns a loaded JSON object, given a JSON file's pod path.

### g.locales

`g.locales(<list of locale identifier>)`

Returns a list of [`Locale class`](http://babel.pocoo.org/docs/locale/#the-locale-class) given a list of locale identifiers.

### g.nav

<div class="badge badge-not-implemented">Not implemented</div>

Returns an object which can be used to create navigation.

### g.static

`g.static(<file path>)`

Returns a `StaticFile` object corresponding to a static file contained within the pod. `<file path>` is the full pod path of the static file. You can access the `path` property of `StaticFile.url` to retrieve an absolute link to the file's serving path.

It is a best practice to *always* refer to static files using the `g.static` tag rather than referring to their URLs directly. This has the benefit of making URL changes easy and Grow will catch broken links to static files at build time.

Prior to using `g.static`, routes must be configured in the `static_dirs` property of `podspec.yaml`.

```jinja
<img src="{{g.static('/static/example.png').url.path}}">
```

`g.static` supports static file localization by way of the `localization` option of the `static_dirs` setting in `podspec.yaml`. If a localized static file exists, it will return the object corresponding to the localized static file. If it doesn't, it will return the object corresponding to the base static file.

```jinja
# Uses the current document's locale.
{{g.static('/static/example.png', locale=doc.locale)}}

# Uses a hardcoded locale.
{{g.static('/static/example.png', locale='de')}}
```

### g.statics

`g.statics(<pod path>)`

Returns a list of StaticFile objects from in a directory within your pod.

```jinja
{% for static_file in g.statics('/source/images/') %}
  <img src="{{static_file.url.path}}">
{% endfor %}
```

### g.url

`g.url(<document path>)`

Returns the URL object for a document, given a document's pod path. Access the `path` property of the URL object to retrieve an absolute link to the document.

```jinja
<a href="{{g.url('/content/pages/index.html').path}}">Home</a>
```

### g.yaml

`g.yaml(<path to yaml>)`

Returns a parsed yaml object, given a yaml file's pod path. Respects translation tagging.

## Filters

### currency

Formats currency in a localized format. Use's [Babel's format_currency](http://babel.pocoo.org/en/latest/api/numbers.html#babel.numbers.format_currency).

```jinja
{{12345|currency('USD')}}
```

### date

Formats localized and non-localized dates. Use's [Babel's format_date](http://babel.pocoo.org/en/latest/dates.html#babel.dates.format_date).

```jinja
{{date_object|date(format='short')}}
{{date_object|date(format='short', locale='ja_JP')}}
{{date_object|date(format="yyyy.MM.dd G 'at' HH:mm:ss zzz")}}
```

### datetime

Formats localized and non-localized datetimes. Use's [Babel's format_datetime](http://babel.pocoo.org/en/latest/dates.html#babel.dates.format_datetime).

### decimal

Formats decimal in a localized format. Use's [Babel's format_decimal](http://babel.pocoo.org/en/latest/api/numbers.html#babel.numbers.format_decimal).

```jinja
{{123.45|decimal()}}
```

### deeptrans

Recursively applies the gettext translation function to strings within a dictionary.

```jinja
{% set content = {
  'key': 'String',
  'item_list': [
      'String 1',
      'String 2'
  ]
} %}
{{content|deeptrans}}
```

### jsonify

Converts a dictionary into JSON.

```jinja
{{dict_object|jsonify}}
```

### markdown

Renders Markdown content into HTML. Use in conjunction with the `safe` filter to render HTML to a page.

```jinja
{{markdown_content|markdown}}
{{markdown_content|markdown|safe}}
```

### number

Formats numbers in a localized format. Use's [Babel's format_number](http://babel.pocoo.org/en/latest/api/numbers.html#babel.numbers.format_number).

```jinja
{{1234.567|number}}
```

### percent

Formats percentages in a localized format. Use's [Babel's format_percent](http://babel.pocoo.org/en/latest/api/numbers.html#babel.numbers.format_percent).

```jinja
{{0.123|percent}}
```

### relative

Generates a relative URL (from the perspective of the current document context) from an absolute URL path.

```jinja
{{g.doc('/content/pages/home.yaml').url|relative}}
```

### shuffle

Randomizes the order of items in a list.

```jinja
{{[1,2,3,4,5]|shuffle}}
```

### slug

Creates a slug from text.

```jinja
{{'Hello World'|slug}}
```

### time

Formats localized and non-localized times. Use's [Babel's format_time](http://babel.pocoo.org/en/latest/dates.html#babel.dates.format_time).
