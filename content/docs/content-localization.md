---
$title: Content localization
$category: Reference
$order: 5
---
# Content localization

[TOC]

Grow lets you localize content by creating and managing fully localized variations of your content. A single content document can hold multiple localized versions of itself. The easiest way to explain how this works is to look at the below examples.

## Markdown body localization

Blueprint `/content/pages/_blueprint.yaml`

    path: /{slug}/
    view: /views/pages.html

    localization:
      path: /{locale}/{slug}/
      default_locale: en
      locales:
      - en
      - de
      - fr
      - it

Document `/content/pages/welcome.md`

    ---
    $title: Hello, Grow localization!
    ---
    # Welcome!
    ---
    $locale: de
    $slug: wilkommen
    ---
    # Willkommen!
    ---
    $locale: fr
    ---
    # Bienvenue!

This example builds to the following pages:

- /welcome/
- /de/wilkommen/ (built to a different path because the built-in `$slug` value is overridden)
- /fr/welcome/
- /it/welcome/

### Cascading behavior

In the above example, you might notice that the content document doesn't actually contain a variation for the `it` locale. When the page at `/it/welcome/` is built, its Markdown body will fall back to the root document's content body.

<div class="badge badge-not-implemented">Not implemented</div>

You can control this behavior by modifying the `fallback` key under the `localization` rule in the blueprint.

    path: /{slug}/
    view: /views/pages.html

    localization:
      path: /{locale}/{slug}/
      fallback: strict

When the blueprint is changed to the above example, without changing the content document, the following pages are built:

- /welcome/
- /de/wilkommen/
- /fr/welcome/
- /it/welcome/ (results in a `MissingMarkdownBodyError`)

The possible values for `fallback` are:

    fallback: default
    fallback: strict

## Front matter localization

Front matter can be changed on a per-locale basis. If you've localized some fields, but not all fields that are specified in the blueprint or default locale, the localized fields will be merged with the default locale's fields. This allows you to localize data on a per-locale basis.

    # In document /content/pages/hello.md...

    ---
    $title: Hello World!
    $path: /{slug}/
    $view: /views/pages.html
    $localization:
      path: /{locale}/{slug}/
    foo: bar
    qaz: qux
    ---
    # Hello World!
    ---
    $locale: de
    foo: baz
    ---
    # Hallo Welt!

    # On page /hello/...

    {{doc.foo}}   # bar
    {{doc.qaz}}   # qux

    # On page /de/hello/...

    {{doc.foo}}   # baz
    {{doc.qaz}}   # qux
