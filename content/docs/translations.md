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

[sourcecode:html]
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
[/sourcecode]

Since Grow translations are opt-in instead of opt-out, it's possible to show translated text from a content document right next to untranslated text.

[sourcecode:html]
{{doc.title()}}      <!-- Untranslated -->
{{_(doc.title())}}   <!-- Translated -->
[/sourcecode]

### Content documents

Field names postfixed with an `@` symbol are translatable. Note that you should omit the `@` when referring to the field in a template. The @ is simply used to tag the field for translation in the YAML front matter.

[sourcecode:yaml]
# /content/pages/page.yaml (content document)

$title@: Hello World!

sections:
- title@: Section A        # Extracted for translation.
  content@: A's content.
- title@: Section B        # Extracted for translation.
  content@: B's content.
- title: Section C         # Not extracted for translation.
  content: C's content.

items@:                    # Tagged list of strings.
- Item 1.
- Item 2.
[/sourcecode]

[sourcecode:html]
# /views/pages.html (sample usage in a view)

{% for section in doc.sections %}
  <li>{{_(doc.title)}}     <!-- Translated. -->
  <li>{{doc.content}}      <!-- Not translated. -->
{% endfor %}
[/sourcecode]

### CSV files

Messages can be extracted from CSV files by appending `@` to a header cell's value.

[sourcecode:text]
header1,header2@,header3
Not extracted,Extracted,Not Extracted
[/sourcecode]

## Translator comments

You can provide clarifying details about strings to translators by using translator comments. Upon extraction, translator comments appear alongside their corresponding messages in message catalogs. Translators may then reference the comment in order to produce a more accurate translation.

Translator comments are particularly useful to convey restrictions about a string (such as its length) or to clarify context when a string may be ambiguous.

[sourcecode:yaml]
# Translator comments in YAML.
prop@: Text to translate
prop@#: Comment for translator.
[/sourcecode]

[sourcecode:html+jinja]
# Translator comments in templates.
{#: Comment for translator. #}
<h1>{{_('Text to translate')}}</h1>
[/sourcecode]

## Extracting translations

To extract translations into a message catalog, tag all translatable items as explained above, and then use the `grow translations extract` command. Messages will be extracted to a file `/translations/messages.pot`. The message catalog (__messages.pot__) contains all of your pod's extracted messages.

This file can then be used to create translation catalogs manually using a PO file editor, or integrated with a translation provider such as Google Translator Toolkit.

[sourcecode:bash]
grow translations extract
[/sourcecode]

Extracted translations can also be audited to find content that is untagged for translation.

[sourcecode:bash]
grow translations extract --audit
[/sourcecode]

## Compiling translations

Grow automatically recompiles translations when the development server starts, builds a pod, and during deployment. Translations must be recompiled before they're visible on your site.

## Importing translations

Grow can import translation PO files from external sources. Currently Grow expects a zip file containing one directory named after its locale. Within each directory should be a `messages.po` file. Alternatively, you can specify a directory instead of a zip file.

[sourcecode:text]
# Structure of source zip file.

/foo.zip
  /de
    /messages.po
  /it/
    /messages.po
[/sourcecode]

[sourcecode:bash]
grow translations import_translations --source=<path to zip file or directory of locales>
[/sourcecode]

## Untranslated content

To help find content that is in use, but not yet translated you can generate a summary of the missing translations.

[sourcecode:bash]
# Builds pod and shows untranslated strings.
grow build --locate-untranslated
[/sourcecode]

You can also update the configuration in your podspec to prevent specific deployments when there are untranslated content.
