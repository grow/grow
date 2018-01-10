---
$title: Directory structure
$category: Reference
$order: 0
---
[TOC]

Grow sites are encapsulated into directories that follow a specific structure. These directories are called "pods". Grow uses the configuration files and the structure of files in each pod to declaratively build your site. Your pod is your site: its content, the structure of its URLs, the translations, redirect behavior, etc. Everything needed by your site is in a pod.

Each pod is a Git repo, and each pod contains all the files used to build your site. Pods contain source files, but upon deployment, Grow deploys only what's needed to serve your site. Sources and other "internal" files are never deployed.

## Example structure

Here's an example pod. Folders and files marked with __*__ are *builtins*, and their names cannot change.

```bash
├──  /build                        # Where your site is built by default.
├──  /content*                     # All your content.
|    ├──  /pages                   # A content collection.
|         ├──  /_blueprint.yaml*   # A blueprint.
|         ├──  /about.md           # A content document.
|         ├──  /contact.md
|         └──  /index.md
|    └──  /posts
|         ├──  /_blueprint.yaml*
|         ├──  /my-first-post.md
|         └──  /hello-grow.md
├──  /dist                         # Compiled files like minified js and css.
|    ├──  /css                     # Used for static serving of minified files.
|         └──  /composite
|              ├──  global.min.css
|              └──  main.min.css
|    └──  /js
|         └──  /composite
|              ├──  global.min.js
|              └──  main.min.js
├──  /partials*                    # Partial files.
|    └──  /hero
|         ├──  /hero.html
|         ├──  /hero.js
|         └──  /hero.sass
├──  /source                       # Source files.
|    ├──  /js
|         └──  /composite
|              ├──  /global.js
|              └──  /main.js
|    └──  /sass
|         └──  /composite
|              ├──  /global.sass
|              └──  /main.sass
├──  /static                       # Static files.
|    ├──  /images
|         └──  /favicon.png
├──  /translations*                # All your translation data.
|    ├──  /messages.pot            # Message catalog template.
|    └──  /de
|         └──  /messages.po        # A message catalog.
|    └──  /fr
|         └──  /messages.po
|    └──  /it
|         └──  /messages.po
├──  /views*                       # Front end views.
|    └──  /base.html
|    └──  /pages.html
|    └──  /posts.html
├──  /package.json                 # JS dependencies.
└──  /podspec.yaml*                # Pod specification.
```
