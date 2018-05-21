---
$title: Content localization
$category: Reference
$order: 1.07
---
[TOC]

In addition to controlling [site-wide localization]({{g.doc('/docs/content-localization/').url.path}}#localization) in podspec.yaml, you can create and manage fully localized content at the collection-level or the document-level.

## Front matter localization

You can localize front matter data on a per-locale basis. If you've localized some fields, but not all fields that are specified in the blueprint or default locale, the localized fields will fall back to default locale's fields, cascading from a localized version down to the default version.

```yaml
title@: Title
title@fr: Title in FR
body@: Body
body@fr: Body for FR
caption@: Caption
```

```jinja
# Default
{{doc.title}} -> Title
{{doc.body}} -> Body
{{doc.caption}} -> Caption

# FR
{{doc.title}} -> Title in FR
{{doc.body}} -> Body for FR
{{doc.caption}} -> Caption
```

## File based localization

Similar to the idea of using the `@locale` localization in the front matter, file names can also be used to manage the localization.

The file naming should follow the [CLDR codes for locales][icu] (case sensitive to support all file systems). For example, files should be named `page@en_GB.yaml` instead of `page@en_gb.yaml`.

```yaml
# Content /content/pages/presentation.yaml
title@: Title
body@: Body
caption@: Caption
```

```yaml
# Content /content/pages/presentation@fr.yaml
title: Title in FR
body: Body for FR
```

```jinja
# Default
{{doc.title}} -> Title
{{doc.body}} -> Body
{{doc.caption}} -> Caption

# FR
{{doc.title}} -> Title in FR
{{doc.body}} -> Body for FR
{{doc.caption}} -> Caption
```

## Locale class

Grow's `Locale` objects subclass the [Babel project's Locale class](http://babel.pocoo.org/en/latest/locale.html#the-locale-class), providing access to some useful data. Grow validates locales and only accepts locales from the [Common Locale Data Repository (CLDR)](http://unicode.org/cldr/), which uses ICU.

[A full list of compatible locales can be found here][icu].

```yaml
# Page /de/hello/
{{doc.locale.get_language_name('en')}}       # German.
{{doc.locale.get_language_name('de')}}       # Deutsch.
```

[icu]: http://www.localeplanet.com/icu/
