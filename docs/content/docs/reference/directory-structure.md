---
$title: Directory structure
$category: Reference
$order: 1.01
---
# Directory structure

Grow sites are encapsulated into directories that follow a specific structure.
These directories are called "pods". Grow uses the configuration files and the
structure of files in each pod to declaratively build your site.

Pods contain source files, but for deployment, Grow builds only what's needed to
serve your site. Sources and other "internal" files are never built to the
output directory.

## Example structure

- Items marked with \* are inbuilt, and their names cannot change.
- Other items aren't required by Grow, but are often found by convention.

```bash
├──  /build                        # Default location for builds.
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
├──  /source                       # Frontend source files.
|    ├──  /js
|         └──  /composite
|              ├──  /global.js
|              └──  /main.js
|    ├──  /sass
|         └──  /composite
|              ├──  /global.sass
|              └──  /main.sass
|    └──  /static                  # Static files.
|         └──  /images
|              └──  /favicon.png
├──  /translations*                # All your translation data.
|    ├──  /messages.pot            # Message catalog template.
|    └──  /de
|         └──  /messages.po        # A message catalog.
|    └──  /fr
|         └──  /messages.po
|    └──  /it
|         └──  /messages.po
├──  /views*                       # Jinja templates.
├──  /partials*                    # Partial templates.
|    └──  /hero
|         ├──  /hero.html
|         ├──  /hero.js
|         └──  /hero.sass
|    └──  /base.html               # Base template for rendering partials.
|    └──  /pages.html
|    └──  /posts.html
├──  /package.json                 # JS dependencies.
└──  /podspec.yaml*                # Pod specification.
```
