---
$title: Documents
$category: Reference
$order: 4
---

# Content documents

[TOC]

All content in Grow is stored inside __content documents__. Content documents are Markdown and YAML files in a pod's `/content/<collection>` directory.

Documents optionally have a `path` property which allows the document to be exposed as a page in your site. If a document does not have a `path`, it is considered to be a partial document and can be included and re-used by other documents.

## Anatomy

### File types

Aside from the *_blueprint.yaml* folder, files in a content collection's directory are treated as a content documents. Grow accepts content documents in the following formats, indicated by their file extensions:

  - HTML (`.html`)
  - Markdown (`.md`)
  - YAML (`.yaml`)

### Document path

The __document path__ of a content document is its path relative to the pod's `/content/` directory. For example, a document whose [pod path](#) is `/content/pages/welcome.md` would have a document path of __pages/welcome.md__.

### Front matter

YAML front matter is YAML metadata that is prepended to a document's body.

Front matter contains fields. Field names prefixed with a dollar sign ($) are ones which are built-in to Grow. Front matter is encapsulated by three dashes (`---`). From views, fields can be accessed using `{{doc.<field name>}}` where <field name> is the name of the field. The dollar sign prefix should be omitted from field names accessed using template variables.

As long as a blueprint specifies a document's `view` and its `path`, including YAML front matter in a content document is optional.

### Body

A document's body is the stuff that comes after its YAML front matter. For Markdown-formatted documents, Grow provides a shortcut for accessing rendered HTML using `{{doc.html}}` (see the `html` API function below). The unprocessed body contents can be accessed with `{{doc.body}}`.

### Rendering and serving

Content documents are servable if they have a `path` (the URL path the document should be served at) and a `view` (the template used to render the document). By default, `path` and `view` are inherited from the document's blueprint.

If the blueprint does not have a `path` and a `view` set, you may specify `$path` and `$view` at the document-level. This also means that you can override the `$path` and `$view` on a document-by-document basis.

[sourcecode:yaml]
$path: /about/              # Serves this document at /about/.
$view: /views/base.html     # Renders this document with /views/base.html.
[/sourcecode]

## Example documents

### Markdown body

Markdown-formatted documents can have optional YAML front matter, which is delimited using `---`.

[sourcecode:yaml]
# /content/pages/foo.md

​---
$title: Hello, Grow!
$category: Get Started
​---
# Welcome to Grow!

This is a [Markdown](http://daringfireball.net/projects/markdown/) document.

- I can use...
- ... Markdown syntax...
- ... to write my content.
[/sourcecode]

### YAML body

YAML-formatted documents never use a separate YAML front matter. `{{doc.html}}` and `{{doc.body}}` are both `None` for YAML-formatted content documents.

[sourcecode:yaml]
# /content/pages/bar.yaml

$title: Hello, Grow!
$category: Get Started

key1: value1
key2: value2
[/sourcecode]

### HTML body

HTML-formatted documents have YAML front matter and an HTML body. As you'd expect, `{{doc.html}}` yields the HTML source for this document, and you'd likely want to use this as `{{doc.html|render|safe}}` in order to render the HTML within the tag's context.

HTML-formatted documents are particularly useful when a content document has its own, unique presentation, that's closely coupled to its content structure. For example, if your collection has an index page, and if the index page has its own unique presentation that is never used anywhere else on the site, the index content document could define its own HTML template unique to itself.

[sourcecode:jinja]
# /content/pages/index.html

​---
$title: Hello, Grow!
$category: Get Started

sections:
- title: Section 1
  text: Lorem ipsum dolor sit amet.
- title: Section 2
  text: Lorem ipsum dolor sit amet.
- title: Section 3
  text: Lorem ipsum dolor sit amet.
​---
{% for section in doc.sections %}
  <h2>{{section.title}}</h2>
  <p>{{section.text}}
{% endfor %}
[/sourcecode]

## Functions

There are several API functions available for documents. These are implemented as functions rather than properties because they accept optional parameters.

### next

`next(<document list>)`

Returns the next document from a list of documents. If no list is provided, the default document ordering within a collection is used. If there is no next document, `None` is returned.

[sourcecode:jinja]
# Returns the next document from the default list of documents.
{{doc.next()}}                     # <Document>

# Returns the next document from a custom list of documents.
{% set doc1 = g.doc('/content/pages/foo.md') %}
{% set doc2 = g.doc('/content/pages/bar.md') %}
{{doc.next([doc1, doc, doc2])}}    # <Document (/content/pages/bar.md)>
[/sourcecode]

### prev

`prev(<document list>)`

Opposite of `next`. Returns the previous document from a list of documents. If no list is provided, the default document ordering within a collection is used. If there is no previous document, `None` is returned.

    # Returns the previous document from the default list of documents.
    {{doc.prev()}}                     # <Document>

    # Returns the previous document from a custom list of documents.
    {% set doc1 = g.doc('/content/pages/foo.md')
    {% set doc2 = g.doc('/content/pages/bar.md')
    {{doc.prev([doc1, doc, doc2])}}    # <Document (/content/pages/foo.md)>

### titles

A function that returns a title, given a title name. Allows for cascading titles. Useful for giving the document a different title in different contexts (for example, a breadcrumb or a side menu). If the parameter is omitted or None, the document's canonical title is used.

[sourcecode:jinja]
{{doc.titles('nav')}}

# This sample YAML front matter...

$title: Example Hello World Document
$titles:
  nav: Hello World
  breadcrumb: Hello World Document

# ...produces the following results.

{{doc.titles('nav')}}          # Hello
{{doc.titles('breadcrumb')}}   # Hello World Document
{{doc.titles('unknown')}}      # Example Hello World Document
{{doc.title()}}                # Example Hello World Document
[/sourcecode]

## Properties

Documents have a few built-in properties that cannot be overwritten by configs.

### base

The basename (minus extension) of the document's file.

    # In document /content/pages/foo.md
    {{doc.base}}        # foo

### collection

A reference to the document's collection.

    # In document /content/pages/foo.md
    {{doc.collection}}  # <Collection (/content/pages/)>

### html

Returns the document's body (for `.md` documents, the Markdown body) rendered as HTML.

    {{doc.html|safe}}  # Avoid escaping the HTML by piping to the "safe" filter.

### locale

Returns the document's [Locale object](http://babel.edgewall.org/wiki/ApiDocs/babel.core#babel.core:Locale).

    {{doc.locale}}                           # Locale object.

    # Display name of the document's locale in the document's language.
    {{doc.get_display_name(doc.locale)}}

    # Display name of the document's locale in English.
    {{doc.get_display_name('en')}}

### locales

Returns a list of [Locale objects](http://babel.edgewall.org/wiki/ApiDocs/babel.core#babel.core:Locale) for the document.

    {{doc.locales}}

### title

Returns the document's canonical title.

    {{doc.title}}

### url

The document's URL object.

    {{doc.url.path}}       # The serving path to the document.

## Built-in fields

Built-in fields carry special meaning that can affect various aspects of building your site. The values of built-in fields can change things such as a tag's output in the template API or the routes served by your site.

### $category

<div class="badge badge-not-implemented">Not implemented</div>

The category the document falls into.

    $category: Get Started

### $hidden

Whether to hide the document when querying for documents with the `g.docs` tag. Note that even if a document is marked hidden, it will still be rendered and served at its URL.

    # Document will not show up in g.docs() results.
    $hidden: true

### $localization

Specify custom localization rules for this document only. Overrides the collection's `localization` configuration.

    # Localized documents will have a custom path.
    $localization:
      path: /foo/{locale}/{base}/

    # Override the locales this document is available in.
    $localization:
      locales:
      - de
      - it
      - fr

### $order

Specify the order for the collection's default document order. Negative and decimal values are allowed.

    $order: 2

### $parent

Specify the parent document in terms of content hierarchy. Used to auto-generate navigation and content relationships.

    # Document /content/pages/foo.md becomes the parent.
    $parent: /content/pages/foo.md

### $path

The serving path to make the document available at. By default, individual documents inherit the path specified by their blueprint. However, it can be overriden by specifying `$path` at the document-level.

    # In document /content/pages/foo.md

    # Makes the document available at /foo/bar/.
    $view: /foo/bar/

    # Makes the document available at /foo/.
    $view: /{base}/

### $slug

Override the document's slug. By default, the document's slug is derived by slugifying its canonical title.

    $slug: foo-bar-baz

### $title

The document's canonical title.

    $title: Canonical Title

### $titles

Specify custom titles for the document to be used in different contexts and by macros. Used by the `{{doc.titles()}}` function.

    $title: Really Long Canonical Title
    $titles:
      breadcrumb: Breadcrumb Title
      nav: Nav Title

### $view

The view to use when rendering the page for this document. By default, individual documents inherit the view specified by their blueprint. However, it can be overriden by specifying it at the document-level.

    # Renders the document with the template at /views/pages.html
    $view: /views/pages.html

<!--

## Custom fields
## Document forms

When adding or editing content documents using a UI (and when validatindocuments) forms describing the content document's structure can be automatically generated by inspecting both the document and its blueprint.

### Fields inherited from blueprints

Input fields will be created for each field present in the document's blueprint. All documents in the same collection will inherit fields from the collection's blueprint.

### Document-specific fields

Documents can also specify their own fields if a specific document has more content than other documents within the same collection. Simply add a new field to the document's front matter to use it.

`/content/people/_blueprint.yaml`

[sourcecode:yaml]
title: People
view: /views/people.html

fields:

- name:
    title: Name
    type: text
- age:
    title: Age
    type: number
- color:
    title: Favorite colors
    type: color
    multiple: yes
[/sourcecode]

`/content/people/john.md`

[sourcecode:yaml]
  ---
  $title: John

  name: John Smith
  age: 25
  color: rgb(0, 0, 128)
  ---
  This is the bio for John. It's Markdown-formatted, but it's so short that doesn't really matter.
[/sourcecode]
