---
$title: Collections
$category: Reference
$order: 3
---
# Content collections

[TOC]

All content in Grow is stored as flat files in your pod's `/content/` directory. Content is grouped into __collections__, and each collection contains a single __blueprint__ and many __documents__. Blueprints describe the structure of all documents in the collection.

Grow makes it easy to separate content from presentation, but ultimately leaves the choice up to you. Content documents can be associated with URLs and with views (so they represent pages in your site), or not. Content documents without URLs are simply used internally, and can be referenced by other content documents.

## Blueprints

Every content collection must have a blueprint. Blueprints define how content is structured, displayed, and served. Blueprints are stored as YAML files in your pod's *content* directory.  For example, a blueprint for a collection "people" would be `/content/people/_blueprint.yaml`

[sourcecode:yaml]
path: /people/{slug}/              # The URL path format for content.
view: /views/people.html           # The template to use.

localization:                      # Overrides localization from podspec.yaml.
  path: /{locale}/people/{slug}/
  locales:
  - de
  - fr
  - it

fields:                            # The content structure (currently unimplemented).
- name:
    title: Name
    type: text
- age:
    title: Age
    type: number

categories:                        # Content categories (unimplemented).
- Teachers
- Students
[/sourcecode]

### path

Specifies the URL path format for content in this collection. If `path` is omitted, content in this collection will not be generated into pages. If `path` is specified, `view` is a required field.

  - {base}
  - {date}
  - {locale}
  - {parent}
  - {slug}

### view

Specifies which template should be used to render content in this collection. If `view` is specified, `path` is a required field.

[sourcecode:yaml]
# Documents in this collection will use the following template.
view: /views/pages.html
[/sourcecode]

### localization

Localization configuration for content in this collection.

#### path

Specifies a URL path format for localized content. By specifying both `path` and `localization:path`, you can use different formats for the URL paths for "root" and localized content.

[sourcecode:yaml]
path: /{locale}/people/{slug}/
[/sourcecode]

#### locales

Specifies a list of locales that documents in this collection are available in. Each document's *path* will be expanded using *locales* to derive the URLs that the document is available at.

[sourcecode:yaml]
locales:
- de
- fr
- it
[/sourcecode]

### categories

The `categories` key contains a list of categories that documents inside the collection can fall into. A collection's categories can be used in conjunction with the `g.categories` template function to iterate over the documents in the collection, grouped by category.
