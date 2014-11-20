---
$title: Content localization
$category: Reference
$order: 5
---
# Content localization

[TOC]

In addition to controlling site-wide localization in podspec.yaml, you can create and manage fully localized content at the collection-level or the document-level. Each content document is capable of holding multiple localized versions of itself. The easiest way to explain how this works is to look at the below examples.

## Markdown body localization

[sourcecode:yaml]
# Blueprint /content/pages/_blueprint.yaml

path: /{slug}/
view: /views/pages.html

# Overrides localization config from podspec.yaml.
localization:
  path: /{locale}/{slug}/
  default_locale: en
  locales:
  - en
  - de
  - fr
  - it
[/sourcecode]

[sourcecode:yaml]
# Document /content/pages/welcome.md

​---
$title@: Hello, Grow localization!
​---
Welcome!
​---
$locale: de
$slug: wilkommen
​---
Willkommen!
​---
$locale: fr
​---
Bienvenue!
[/sourcecode]

This example builds the following pages:

- /welcome/
- /de/wilkommen/ (built to a different path because the built-in `$slug` value is overridden)
- /fr/welcome/
- /it/welcome/

## Front matter localization

You can localize front matter data on a per-locale basis. If you've localized some fields, but not all fields that are specified in the blueprint or default locale, the localized fields will be merged with the default locale's fields, cascading from a localized version down to the default version.

[sourcecode:yaml]
# Document /content/pages/hello.md

​---
$title: Hello World!
$path: /{slug}/
$view: /views/pages.html
$localization:
  path: /{locale}/{slug}/
foo: bar
qaz: qux
​---
Hello World!
​---
$locale: de
foo: baz
​---
Hallo Welt!
[/sourcecode]

[sourcecode:jinja]
# Page /hello/

{{doc.foo}}         # bar
{{doc.qaz}}         # qux
{{doc.locale}}      # Locale('en')

# Page /de/hello/

{{doc.foo}}         # baz
{{doc.qaz}}         # qux
{{doc.locale}}      # Locale('de')
[/sourcecode]

## Locale class

Grow's `Locale` objects subclass the [Babel project's Locale class](http://babel.pocoo.org/docs/locale/), providing access to some useful data. Grow validates locales and only accepts locales from the [Common Locale Data Repository (CLDR)](http://unicode.org/cldr/).

[sourcecode:yaml]
# Page /de/hello/
{{doc.locale.get_language_name('en')}}       # German.
{{doc.locale.get_language_name('de')}}       # Deutsch.
[/sourcecode]
