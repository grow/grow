---
$title: Translations
$category: Reference
---
# Translations

## Translatable items

Items deemed "translatable" are ones which contain text which can be extracted by Grow into message catalogs for translation. Message catalogs can be used to generate translated content.

Grow takes a __"what you tag is what you translate"__ approach: only things that you deem translatable will be extracted for translation, and then subsequently translated upon request.

### Content documents

Fields marked with `translatable: yes` in a collection's blueprint are translatable.

`/content/pages/_blueprint.yaml`
    
    path: /pages/{language}/{slug}
    view: /views/pages.html

    fields:
    - callout:
        title: Callouts
        type: text
        translatable: yes

### Views

UI strings (and other text) in views are translatable. UI strings must be tagged with a template function that indicates the text is translatable. This template function has been aliased to `{{_(<text>)}}`.

`/views/pages.html`

    <!DOCTYPE html>
    <meta charset="utf-8">
    <title>{{_('Hello World!')}}</title>
    <h1>{{_('Page Title')}}</h1>

    <ul>
      {% for callout in g.doc.callouts %}
        <li>{{callout.title}} – {{callout.description}}
      {% endfor %}
    </ul>

## Extracting translations

To extract translations into a message catalog, tag all translatable items as explained above, and then use the `grow extract` command. Messages will be extracted to a file `/translations/messages.pot`. The message catalog (__messages.pot__) contains all of your pod's extracted messages.

Note that message extraction does not include the Markdown body of a content document – translated Markdown bodies are stored within the content documents themselves.
