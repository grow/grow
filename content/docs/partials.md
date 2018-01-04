---
$title: Partials
$category: Style Guide
$order: 1
---
[TOC]

Partial templates are a powerful concept that permit site architects to divide a design up into sections, and then freely rearrange and reuse those designs throughout the site.

Most pages that can be divided up into discrete sections (such as a header, content area – or collection of various content areas in order, and a footer) should be implemented using partials.

## Setting up the partial system

Setup the partial system by adding a partial loop to your page template.

[sourcecode:jinja]
{# /views/base.html #}
{% if doc.partials %}
  {% for field in doc.partials %}
    {% if not field.partial %}
      {% continue %}
    {% endif %}

    {# Render the partial with the values in {{partial}}. #}
    {% set partial_filename = field.partial|expand_partial %}
    {% with partial = field %}
      {% include partial_filename with context %}
    {% endwith %}
  {% endfor %}
{% else %}
  {{doc.html|safe}}
{% endif %}
[/sourcecode]

### Create partials in the `/partials` directory.

[sourcecode:jinja]
{# /partials/hero/hero.html #}
<div class=”hero”>
   <h1 class=”hero__title”>{{_(partial.title)}}</h1>
</div>
[/sourcecode]

[sourcecode:jinja]
{# /partials/about-me/about-me.html #}
<div class=”about-me”>
   <h2 class=”about-me__title”>{{_(partial.title)}}</h2>
   <p>{{_(partial.description)}}</p>
</div>
[/sourcecode]

[sourcecode:jinja]
{# /partials/footer/footer.html #}
<div class=”footer”>
   <p class=”footer__copyright>{{_(partial.copyright)}}</p>
</div>
[/sourcecode]

### Add structured partials to your page front matter

[sourcecode:yaml]
# /content/pages/about.yaml
$view: /views/base.html
$path: /about/

partials:
- partial: hero
  title@: My hero
  image: !gstatic /static/images/about_me.jpg
- partial: about-me
  title@: About me
  description@: I am a grow.io user!
- partial: footer  
  copyright@: 2017 Mysite.com
[/sourcecode]

Now your “about” page will render a hero, about-me and footer partial.   Easily reuse partials across your site pages.

## Naming Partials

Name partials in a generic way. The name of the partial should not be coupled to a specific page if possible, but rather the partials’ design.

Taking advantage partial system
Partials can be easily reused across different pages.  You can even selectively render different partials per locale.

The following example would should show a different “about” page for Canada.

[sourcecode:yaml]
# /content/pages/about.yaml
$view: /views/base.html
$path: /about/

partials:
- partial: hero
  title@: My hero
  image: !gstatic /static/images/about_me.jpg
- partial@en_US: about-me
  title@: About me
  Description: I am a grow.io user!
- partial@en_CA: trip
  title@: My trip to Canada
- partial: footer
  copyright@: 2017 Mysite.com
[/sourcecode]

## Keep it DRY

Don’t repeat yourself and duplicate similar partials.  Instead try to create multiple variations within same partial by passing configuration flags or by passing css classes.

[sourcecode:yaml]
# /content/pages/about.yaml
partials:
- partial: hero
  title@: My hero
  class@ja_JP: carousel--large
  carousel_disabled@en_CA: true
[/sourcecode]
