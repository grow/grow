---
$title: Directory structure
$category: Reference
$order: 0
---
# Pod directory structure

Grow sites are encapsulated into directory structures known as "pods". Grow uses the configuration files and the structure of files in each pod to predictably build your site.

Your pod specification determines everything about your site: its content, the structure of its URLs, the 

## Directory structure

    .
    ├──  /content
    |    ├──  /pages
    |    |    └──  /podspec.yaml
    |    ├──  /posts
    |    └──  /podspec.yaml
    ├──  /media
    ├──  /translations
    |    ├──  /messages.pot
    |    └──  /de
    |         └──  /messages.po
    |    └──  /de
    |         └──  /messages.po
    ├──  /views
    |    └──  /_base.html
    |    └──  /pages.html
    |    └──  /posts.html
    └──  /podspec.yaml

## Content collections

### Blueprints

### Content documents

## Views

## Translations
