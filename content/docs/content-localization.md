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
      locales:
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

In this example, you might notice that the content document doesn't actually contain a variation for the `it` locale. When the page at `/it/welcome/` is built, its Markdown body will fall back to the root document's content body.

You can control this behavior by modifying the `fallback` key under the `localization` rule in the blueprint.

    path: /{slug}/
    view: /views/pages.html

    localization:
      path: /{locale}/{slug}/
      fallback: strict
      locales:
      - de
      - fr
      - it

When the blueprint is changed to the above example, without changing the content document, the following pages are built:

- /welcome/
- /de/wilkommen/
- /fr/welcome/
- /it/welcome/ (results in a `MissingMarkdownBodyError`)

The possible values for `fallback` are:

    fallback: default
    fallback: strict

## Front matter localization
