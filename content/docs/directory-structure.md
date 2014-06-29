---
$title: Directory structure
$category: Reference
$order: 0
---
# Pod directory structure

[TOC]

Grow sites are encapsulated into directories that follow a specific structure. These directories are called "pods". Grow uses the configuration files and the structure of files in each pod to declaratively build your site. Your pod is your site: its content, the structure of its URLs, the translations, redirect behavior, etc. Everything needed by your site is in a pod.

Each pod is a Git repo, and each pod contains all the files used to build your site. Pods contain source files, but upon deployment, Grow deploys only what's needed to serve your site. Sources and other "internal" files are never deployed.

## Pod directory structure

Here's an example pod. Folders and files marked with __*__ are *builtins*, and their names cannot change.

[sourcecode:txt]
├──  /content*                     # All your content.
|    ├──  /pages                   # A content collection.
|         ├──  /_blueprint.yaml*   # A blueprint.
|         ├──  /about.md           # A content document.
|         ├──  /contact.md
|         └──  /index.md
|    └──  /posts
|         ├──  /_blueprint.yaml
|         ├──  /my-first-post.md
|         └──  /hello-grow.md
├──  /source                       # Source files.
|    ├──  /sass
|         ├──  /_header.sass
|         ├──  /_carousel.sass
|         └──  /main.sass
|    └──  /js
|         ├──  /carousel.js
|         ├──  /main.js
|         └──  /widget.js
├──  /static                       # Static files.
|    └──  /css
|         └──  /main.min.css
|    └──  /js
|         ├──  /jquery.min.js
|         └──  /main.min.js
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
└──  /podspec.yaml*                # Pod specification.
[/sourcecode]
