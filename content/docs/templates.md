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

    {{doc.category}}      # Document's category
    {{doc.title}}         # Document's canonical title.
    {{doc.titles('nav')}} # Document's "nav" title.
    {{doc.html|safe}}     # Document's rendered Markdown body.
    {{doc.foo}}           # Value of the "foo" custom field from the YAML front matter.

### podspec

Refers to the [`podspec.yaml` configuration file]([url('/content/docs/podspec.md')]) and allows you to access pod-wide settings in templates.

    {{podspec.title}}         # Pod's title.
    {{podspec.project_id}}    # Pod's project ID.

## Functions

All built-in functions are prefixed with the `g` namespace.

### g.breadcrumb

`g.breadcrumb(<doc>)`

<div class="badge badge-not-implemented">Not implemented</div>

Returns a list of ancestor documents, in order from oldest to youngest, to produce a breadcrumb for the given document.

    <!-- Produces a breadcrumb for the current page. -->
    <ul>
      {% for item in g.breadcrumb(doc) %}
        <li><a href="{{item.url.path}}">{{item.title('breadcrumb')}}</a>
      {% endfor %}
    </ul>

### g.categories

`g.categories(<collection>)`

Lists content documents within a collection and groups them by their *$category*. Useful for generating navigation and categorized lists of documents.

    {% for category, docs in g.docs('pages') %}
      <h3>{{category}}</h3>
      <ul>
        {% for doc in docs %}
          <li>{{doc.title()}}
        {% endfor %}
      </ul>
    {% endfor %}

### g.doc

`g.doc(<document path>, locale=<locale>)`

Gets a single content document, given its pod path.

    {% set foo = g.doc('/content/pages/index.md') %}
    {{foo}}


    # Returns the fr version of a document.
    {{g.doc('/content/pages/index.md', locale='fr'}}

### g.docs

`g.docs(<collection>, order_by=<field name>, locale=<locale>)`

Searches content documents within a collection.

    <ul>
      {% for doc in g.docs('pages') %}
        <li>{{doc.title}}
      {% endfor %}
    </ul>

### g.nav

<div class="badge badge-not-implemented">Not implemented</div>

Returns an object which can be used to create navigation.

### g.static

`g.static(<file path>)`

Returns the URL object for a static file from the pod's static directory. `<file path>` is the full pod path of the static file. Access the `path` property of the URL object to retrieve an absolute link to the static file.

It is a best practice to refer to static files using the `g.static` tag rather than referring to their URLs directly. This allows Grow to automatically implement efficient cache headers and cache-busting techniques for incremental static file deployments.

    <img src="{{g.static('/static/example.png').path}}">

### g.url

`g.url(<document path>)`

Returns the URL object for a document, given a document's pod path. Access the `path` property of the URL object to retrieve an absolute link to the document.

    <a href="{{g.url('/content/pages/index.md').path}}">Home</a>
