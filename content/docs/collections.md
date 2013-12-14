---
$title: Content collections
$category: Reference
---

# Content collections

All content in Grow is stored as flat files in your pod's __/content/__ directory. Content is grouped into __collections__, and collections contain a single __blueprint__ and __documents__. Blueprints describe the structure of all documents in the collection.

Grow makes it easy to separate content from presentation, but ultimately leaves the choice up to you. Content documents can be associated with URLs and with views (so they represent pages in your site), or not. Content documents without URLs are simply used internally, and can be referenced by other content documents.

## Blueprints

Every content collection must have a blueprint. Blueprints define how content is structured, displayed, and served. Blueprints are stored as YAML files in your pod's *content* directory.  For example, a blueprint for a collection "people" would be `/content/people/_blueprint.yaml`

    path: /people/{slug}
    view: /views/people.html

    fields:
    - name:
        title: Name
        type: text
    - age:
        title: Age
        type: number

    categories:
    - Teachers
    - Students

### path

Specifies the URL path format for content in this collection. If `path` is omitted, content in this collection will not be generated into pages. If `path` is specified, `view` is a required field.

#### Converters

- {language}
- {locale}
- {region}
- {slug}
- {title}

### view

Specifies which template should be used to render content in this collection. If `view` is specified, `path` is a required field.

### fields

Specifies the content structure for documents in this collection. Fields are used to validate the structure of content documents and to provide users with a form for content entry.

#### Properties

- name
- type
- default
- choices (for checkboxes, selects, and radios)
- multiple

#### Fieldtypes

A blueprint can also optionally specify the structure for all of the content within its corresponding collection. When content managers add new documents to the collection, Grow uses the collection's blueprint to generate the form the person uses to enter the content.

Grow supports the following fieldtypes:

- checkbox
- collection
- color
- date
- document
- json
- link
- number
- radio
- select
- text
- textarea
- time
- yaml

#### Built-in fields

The following fields are built-in, and you do not need to specify them in a blueprint. Built-in fields are prefixed with a "$" in a content document's front matter.

- $category – text
- $draft – checkbox
- $hidden – checkbox
- $order – number
- $tags – text (multiple)
- $title – text

### categories

The `categories` key contains a list of categories that documents inside the collection can fall into. A collection's categories can be used in conjunction with the `g.categories` template function to iterate over the documents in the collection, grouped by category.
