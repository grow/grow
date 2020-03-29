---
$title: Partials
$order: 1
---
Partial templates are a powerful concept that permit site architects to divide
a design up into sections, and then freely rearrange and reuse those designs
throughout the site.

Most pages that can be divided up into discrete sections (such as a header,
content area – or collection of various content areas in order, and a footer)
should be implemented using partials.

## Setup

### The partial loop

Partials are rendered by a partial loop that exists in the base Jinja template
(`/views/base.html`). The partial loop resembles the following (though, your
actual partial loop should have more logic to control the conditional display
of partials).

<figcaption>/views/base.html</figcaption>
```jinja
{% set partials = doc.partials or doc.collection.partials %}
{% for partial in partials if partial.partial %}
  {% set template = '/views/partials/{}.html'.format(partial.partial) %}
  {% include template with context %}
{% endfor %}
```

### Templates

Create templates in the `/views/partials` directory.

<figcaption>/views/partials/hero.html</figcaption>
```jinja
<div class="hero {{partial.class}}">
  {% if partial.title %}
    <div class="hero__title">
      {{partial.title}}
    </div>
  {% endif %}
  {% if partial.body %}
    <div class="hero__body">
      {{partial.body}}
    </div>
  {% endif %}
</div>
```

<figcaption>/views/partials/person.html</figcaption>
```jinja
<div class="person {{partial.class}}">
  <div class="person__name">
    <div class="person__name__avatar">
      <img src="{{partial.avatar.url.path}}">
    </div>
    <div class="person__name__title">
      {{partial.title}}
    </div>
  </div>
</div>
```

### Content

Add structured content to your content document's front matter.

<figcaption>/content/pages/index.yaml</figcaption>
```yaml
$view: /views/base.html

partials:

- partial: hero
  title: Welcome
  body: This website's body copy is here.

- partial: person
  title: Scott
  avatar: !g.static /source/images/home/scott.png

- partial: person
  title: Adelaide
  avatar: !g.static /source/images/home/adelaide.png

- partial: person
  title: Steven
  avatar: !g.static /source/images/home/steven.png
```

In this example, the `index` page renders a hero, and three person partials.
The `hero`, and `person` templates can subsequently be reused on other pages.

If the same content is reused, put partial content documents into the
`/content/partials` folder, and then import them into pages.

<figcaption>/content/partials/header.yaml</figcaption>
```yaml
partial: header
logo:
  title: My Site
  image: !g.static /source/images/logo.png
nav:
- doc: !g.doc /content/pages/index.yaml
- doc: !g.doc /content/pages/about.yaml
- url: https://www.github.com/grow/grow
```

<figcaption>/content/pages/about.yaml</figcaption>
```yaml
partials:
- !g.yaml /content/partials/header.yaml
```

For content which you know is on every page, modify the partial loop and add
rendering of an additional set of partials either before or after. This is
typically reserved for the global header and footer.

```
{% with partial = g.doc('/content/partials/header.yaml') %}
  {% if partial.partial %}
    {% set template = '/views/partials/{}.html'.format(partial.partial) %}
    {% include template with context %}
  {% endif %}
{% endwith %}

{# ... the partial loop ... #}

{% with partial = g.doc('/content/partials/footer.yaml') %}
  {% if partial.partial %}
    {% set template = '/views/partials/{}.html'.format(partial.partial) %}
    {% include template with context %}
  {% endif %}
{% endwith %}
```

### Styles

Create corresponding styles encapsulated into a single Sass file.

<figcaption>/source/sass/partials/_hero.sass</figcaption>
```sass
.hero
  margin: 20px 0

.hero__title
  +font-h2

.hero__body
  +font-body
```

## Reuse

Partials can be easily reused across pages, making it easy to implement a
modular design or design system. If several pages all leverage
the same or similar modules, the selective application and mixing and matching
of partials make it possible to easily build a large, templatized site.

<figcaption>/content/pages/about.yaml</figcaption>
```yaml
partials:

- partial: hero
  ...
- partial: columns
  ...
- partial: columns
  ...
- partial: carousel
  ...
- partial: people
  ...
```

<figcaption>/content/pages/products.yaml</figcaption>
```yaml
partials:

- partial: hero
  ...
- partial: carousel
  ...
- partial: columns
  ...
- partial: gallery
  ...
```

### Avoid duplicated partials

Avoid duplicating a partial when a variation can be easily created through
obvious configuration or by adding a simple class.

For example, instead of creating two partials (i.e. `two-columns` and
`three-columns`), create one `partials` column and automatically infer the
number of columns based on the data.

<figcaption>/content/pages/index.yaml</figcaption>
```yaml
...
- partial: columns
  columns:
  - body: Column 1.
  - body: Column 2.
  - body: Column 3.
...
```

<figcaption>/views/partials/columns.html</figcaption>
```jinja
<div class="columns {{partial.class}}">
  {% for column in columns %}
    <div class="columns__column">
      <div class="columns__column__body">
        {{column.body}}
      </div>
    </div>
  {% endfor %}
</div>
```

Another way to create variations is to add classes. For example, if you wanted
to create a variation of the `columns` partial where the first class is large,
leverage the top-level `class` key.

<figcaption>/content/pages/index.yaml</figcaption>
```yaml
...
- partial: columns
  class: columns--large
...
```

<figcaption>/source/sass/partials/_columns.sass</figcaption>
```sass
.columns

.columns--large
  .columns__column
    font-size: huge
```

## Naming

### Guidelines

Choose an obvious, memorable name.

Partials should be named in a concise yet descriptive way. Naming is hard – be
generic, but not too generic. For example, if a design has a
commonly-used "top" or "hero" module, name it `hero`. Or a commonly used
column module, name it `columns`.

Avoid coupling the partial's name to a specific page, unless the
partial's design can in no way be applied elsewhere. If there is a slight
variation between two pages, use a generic name. If a module is unique to a
page and will always be for the forseeable future, you may prefix the partial's
name with the page's basename.

Avoid names that include "count numbers". For example, a `two-column` partial
may eventually grow to be an `x-column` mask.

### Example names

<table>
  <tr>
    <td>basement</td>
    <td>Also known as a "fat footer", a basement usually has navigational links for accessibility/SEO purposes and appears above or below a footer.</td>
  </tr>
  <tr>
    <td>chapter</td>
    <td>A single instance of a "chapter" (a series of icons, eyebrow, title, body copy, buttons, etc.)</td>
  </tr>
  <tr>
    <td>header</td>
    <td>Your website's global header.</td>
  </tr>
  <tr>
    <td>footer</td>
    <td>Your website's global footer.</td>
  </tr>
  <tr>
    <td>hero</td>
    <td>The main module that appears front and center, above the fold.</td>
  </tr>
</table>

## Conditional rendering

In the partial loop example earlier, a partial can be disabled by setting the
top-level `partial` key to `null`. This permits use of Grow's YAML tagging to
conditionally render partials (such as varying by locale or environment).

<figcaption>/content/pages/index.yaml</figcaption>
```yaml
partials:

# Not displayed in the `prod` deployment.
- partial: columns
  partial@env.prod: ~
  ...

# Not displayed in the `ja_JP` locale.
- partial: columns
  partial@ja_JP: ~
  ...

# Only displayed in the `fr_FR` locale.
- partial@fr_FR: columns
  ...
```
