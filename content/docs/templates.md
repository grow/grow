---
$title: Templates
$category: Reference
$order: 2
---

# Templates

[TOC]

Grow templates are stored in a pod's */views/* directory. Templates are processed using the [Jinja2](http://jinja.pocoo.org/docs/) template language. Grow extends Jinja2 with a few variables and functions that make building content-rich web sites more convenient.

Variables have no prefix and are part of the global template scope. Functions are prefixed into the `g` namespace, for example: `g.<function name>`.

## Variables

There are several built-in global variables available to templates. Because these variables are not namespaced, take caution not to overwrite their values.

### doc

The current content document associated with the current page that's being rendered. See the [full documentation for the document API]([url('/content/docs/documents.md')]).

[sourcecode:html+jinja]
{{doc.category}}      # Document's category
{{doc.title}}         # Document's canonical title.
{{doc.titles('nav')}} # Document's "nav" title.
{{doc.html|safe}}     # Document's rendered Markdown body.
{{doc.foo}}           # Value of the "foo" custom field from the YAML front matter.
[/sourcecode]

### env

The rendering environment that exists when the page is being built or served.

    {{env.host}}
    {{env.name}}
    {{env.port}}
    {{env.scheme}}

### podspec

Refers to the [`podspec.yaml` configuration file]([url('/content/docs/podspec.md')]) and allows you to access pod-wide settings in templates.

[sourcecode:html+jinja]
{{podspec.title}}         # Pod's title.
{{podspec.project_id}}    # Pod's project ID.
[/sourcecode]

## Functions

### _

`_(<string>)`

The `_` tag is a special function used to tag strings in templates for both translation and message extraction.

    # Simple translation.
    {{_('Hello')}}

    # A translation with a placeholder.
    {{_('Hello, %(name)s', name='Alice')}

### g.breadcrumb

`g.breadcrumb(<doc>)`

<div class="badge badge-not-implemented">Not implemented</div>

Returns a list of ancestor documents, in order from oldest to youngest, to produce a breadcrumb for the given document.

[sourcecode:html+jinja]
<!-- Produces a breadcrumb for the current page. -->
<ul>
  {% for item in g.breadcrumb(doc) %}
    <li><a href="{{item.url.path}}">{{item.title('breadcrumb')}}</a>
  {% endfor %}
</ul>
[/sourcecode]

### g.categories

`g.categories(<collection>)`

Lists content documents within a collection and groups them by their *$category*. Useful for generating navigation and categorized lists of documents.

[sourcecode:html+jinja]
{% for category, docs in g.docs('pages') %}
  <h3>{{category}}</h3>
  <ul>
    {% for doc in docs %}
      <li>{{doc.title()}}
    {% endfor %}
  </ul>
{% endfor %}
[/sourcecode]

### g.csv

`g.csv(<path to csv>, locale=<identifier>)`

Parses a CSV file and returns a list of dictionaries mapping header rows to values for each row. Optionally use keyword arguments to filter results. This can be particularly useful for using a spreadsheet for localization (where rows represent values for different locales).

[sourcecode:html+jinja]
{% set people = g.csv('/data/people.csv') %}
{% for person in people %}
  <li>{{person.name}}
{% endfor %}
[/sourcecode]

### g.date

`g.date(<DateTime|string>, from=<string>, to=<string>)`

Multipurpose date and time utility function. Capable of both formatting a DateTime as a string and/or parsing a string into a DateTime. Uses [Python date formatting directives](https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior).

    # Returns a DateTime given a string and a format.
    {{g.date('12/31/2000', from='%m/%d/%Y')}}

    # Returns a formatted string given a DateTime.
    {{g.date(date, to='%m')}}

    # Returns a formatted string, given both a string and a format.
    {{g.date('12/31/2000', from='%m/%d/%Y', to='%m')}}

### g.doc

`g.doc(<document path>, locale=<locale>)`

Gets a single content document, given its pod path.

[sourcecode:html+jinja]
{% set foo = g.doc('/content/pages/index.html') %}
{{foo}}

# Returns the fr version of a document.
{{g.doc('/content/pages/index.html', locale='fr'}}
[/sourcecode]

### g.docs

`g.docs(<collection>, order_by=<field name>, locale=<locale>)`

Searches content documents within a collection.

[sourcecode:html+jinja]
<ul>
  {% for doc in g.docs('pages') %}
    <li>{{doc.title}}
  {% endfor %}
</ul>
[/sourcecode]

### g.locales

`g.locales(<list of locale identifier>)`

Returns a list of [`Locale class`](http://babel.pocoo.org/docs/locale/#the-locale-class) given a list of locale identifiers.

### g.nav

<div class="badge badge-not-implemented">Not implemented</div>

Returns an object which can be used to create navigation.

### g.static

`g.static(<file path>)`

Returns the URL object for a static file from the pod's static directory. `<file path>` is the full pod path of the static file. Access the `path` property of the URL object to retrieve an absolute link to the static file.

It is a best practice to refer to static files using the `g.static` tag rather than referring to their URLs directly. This allows Grow to automatically implement efficient cache headers and cache-busting techniques for incremental static file deployments.

[sourcecode:html+jinja]
<img src="{{g.static('/static/example.png').path}}">
[/sourcecode]

### g.url

`g.url(<document path>)`

Returns the URL object for a document, given a document's pod path. Access the `path` property of the URL object to retrieve an absolute link to the document.

[sourcecode:html+jinja]
<a href="{{g.url('/content/pages/index.html').path}}">Home</a>
[/sourcecode]
