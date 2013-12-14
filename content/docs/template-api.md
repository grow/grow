---
$title: Template API
$category: Reference
---

# Template API

Grow templates are stored in a pod's */views/* directory. Templates are processed using the Jinja2 template language. Grow extends Jinja2 with a few variables and functions that make building content-rich web sites more convenient.

## Variables

### g.doc

The current content document associated with the page. Fields of the content document can be accessed using: `{{g.doc.<field name>}}`.

    {{g.doc.title}}
    {{g.doc.html|safe}}
    {{g.doc.category}}

## Functions

### g.entries

`g.entries(<collection>, order_by=<field name>)`

Lists content documents within a collection.

    <ul>
      {% for doc in g.entries('pages') %}
        <li>{{doc.title}}
      {% endfor %}
    </ul>

### g.categories

`g.categories(<collection>)`

Lists content documents within a collection and groups them by their *$category*. Useful for generating navigation menus. 

    {% for category, docs in g.entries('pages') %}
      <h3>{{category}}</h3>
      <ul>
        {% for doc in docs %}
          <li>{{doc.title}}
        {% endfor %}
      </ul>
    {% endfor %}

### g.url

`g.url(<document path>)`

Returns the URL path for a document, given a document's path.

    <a href="{{g.url('/content/pages/index.md')}}">Home</a>

### g.static

`g.static(<file path>)`

Returns the URL path for a static file from the pod's static directory. `<file path>` is the full pod path of the static file.

    <img src="{{g.static('/static/example.png')}}">
