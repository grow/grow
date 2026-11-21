---
$title: Variations
$order: 2
---

## Keep variations in YAML

You may generate different versions of a partial, page, or entire site based on
a condition such as the locale of a page, the build environment (i.e. staging
or production) or the page that a partial is used on. In all cases, variations
should be configured in front matter rather than the template.

<figcaption>/content/pages/gallery.yaml</figcaption>
```yaml
$title@: My Gallery
$title@en_CA@: My Canadian Gallery

partials:
- partial: gallery
  class@fr_FR: gallery gallery--large
  image: !g.static /source/images/image.png
  image@fr_FR: !g.static /source/images/image.png
  image@(en_AU|en_GB): !g.static /source/images/image-celsius.png
```

### Avoid variations in views

Keeping the variations managed in front matter increases maintainability and
further follows the best practice of separating content (YAML/Markdown) from
presentation (Jinja templates). Avoid placing environment and locale logic in
views.

```jinja
{# DONT #}
{% if doc.locale.language == 'en' %}
  <h1>My English title</h1>
{% else %}
  <h1>All other titles</h1>
{% endif %}
```

## Leverage localization groups

If you have several variations to maintain in multiple places, use a
localization group to centrally manage locales in one place, rather than
duplicating the locales in multiple keys.

<figcaption>/content/pages/gallery.yaml</figcaption>
```yaml
...

$localization:
  groups:
    fahrenheit:
    - en_BZ
    - en_US
    celsius:
    - en_GB
    - en_AU
    - en_NZ

...

image: !g.static /source/images/default.png
image@group.fahrenheit: !g.static /source/images/fahrenheit.png
image@group.celsius: !g.static /source/images/celsius.png
```
