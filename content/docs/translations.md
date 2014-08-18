---
$title: Translations
$category: Reference
$order: 7
---
# Translations

[TOC]

## Translatable items

Items that are "translatable" are ones which contain text which can be extracted by Grow into message catalogs for translation. Message catalogs can be used to generate translated content.

Grow takes a __what you tag is what you translate__ approach: only things that you deem translatable will be extracted for translation, and then subsequently translated upon request.

### Views

UI strings (and other text) in views are translatable. UI strings must be tagged with a template function that indicates the text is translatable. This template function, `gettext`, has been aliased to `{{_(<text>)}}`.

    <!-- /views/pages.html -->

    <!DOCTYPE html>
    <meta charset="utf-8">
    <title>{{_('Hello World!')}}</title>
    <h1>{{_('Page Title')}}</h1>

    <ul>
      {% for callout in g.doc.callouts %}
        <li>{{_(callout.title)}} – {{_(callout.description)}}
      {% endfor %}
    </ul>

    <!-- Using Python-format placeholders. -->
    <p>{{_('Posted: %(date)s', date='12/25/86')}}

Since Grow translations are opt-in instead of opt-out, it's possible to show translated text from a content document right next to untranslated text.

    {{doc.title()}}      <!-- Untranslated -->
    {{_(doc.title())}}   <!-- Translated -->

### Content documents

Field names postfixed with an `@` symbol are translatable. Note that you should omit the `@` when referring to the field in a template. The @ is simply used to tag the field for translation in the YAML front matter.

    # /content/pages/foo.md (YAML front matter)

    ---
    $title@: Hello World!

    sections:
    - title@: Section A        # Extracted for translation.
      content@: A's content.
    - title@: Section B        # Extracted for translation.
      content@: B's content.
    - title: Section C         # Not extracted for translation.
      content: C's content.
    ---

    # /views/pages.html (sample usage in a view)

    {% for section in doc.sections %}
      <li>{{_(doc.title)}}     <!-- Translated. -->
      <li>{{doc.content}}      <!-- Not translated. -->
    {% endfor %}

## Extracting translations

To extract translations into a message catalog, tag all translatable items as explained above, and then use the `grow extract` command. Messages will be extracted to a file `/translations/messages.pot`. The message catalog (__messages.pot__) contains all of your pod's extracted messages.

This file can then be used to create translation catalogs manually using a PO file editor, or integrated with a translation provider such as Google Translator Toolkit.

    $ grow extract ~/my-codelab/

    Extracted 128 messages from 3 files to: /translations/messages.pot
    Creating catalog 'translations/de/LC_MESSAGES/messages.po' based on 'translations/messages.pot'
    Creating catalog 'translations/fr/LC_MESSAGES/messages.po' based on 'translations/messages.pot'
    Creating catalog 'translations/it/LC_MESSAGES/messages.po' based on 'translations/messages.pot'
    Creating catalog 'translations/ja/LC_MESSAGES/messages.po' based on 'translations/messages.pot'

## Compiling translations

Grow automatically recompiles translations upon server start and deployment. Translations must be recompiled before they're visible on your site.
