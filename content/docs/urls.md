---
$title: URLs, serving paths, and permalinks
$category: Reference
$order: 4.1
---
# URLs, serving paths, and permalinks

[TOC]

Grow provides a flexible way to configure the URL serving paths for your site's routes. By leveraging the URL path configuration features, you can easily create clean, maintainable, and flexible URLs for all of your site's routes.

## Philosophy

Serving paths and filesystem paths do *not* need to match one-to-one. This is an explicit capability that exists to remove the need to need to name internal files a specific way. Because internal file paths do not need to match serving paths, you can change the URL of content at any time without renaming files or performing find and replace operations throughout your site.

## Configuring URLs

There are three places URLs are configured: `podspec.yaml`, blueprints, and content documents.

### Content document path formatters

Use these formatters to configure serving paths for documents either in a content document or its blueprint.

| Path formatter
|-|-|
| `{base}` | The document's basename.
| `{collection.root}` | The document's collection's root.
| `{date}` | The document's date.
| ` {locale}` | The document's locale (or its alias, if one exists).
| `{root}` | The pod's root as defined in podspec.yaml.
| `{slug}` | The document's slug.

#### Examples

[sourcecode:yaml]
# In a collection's _blueprint.yaml
path: /pages/{slug}/
path: /pages/{base}/
path: "{root}/pages/{base}/"
localization:
  path: /{locale}/pages/{slug}/

# In document.yaml (use '$path' instead of 'path')
$path: /pages/home/
$localization:
  path: /{locale}/pages/home/
[/sourcecode]

### Static file path formatters

Use these formatters to configure serving paths for static files in `podspec.yaml`.

| Path formatters
|-|-|
| ` {locale}` | The static file's locale (or its alias, if one exists).
| `{root}` | The pod's root as defined in podspec.yaml.

#### Examples

[sourcecode:yaml]
# In podspec.yaml
static_dirs:
- static_dir: /source/images/
  serve_at: /static/images/
  localization:
    static_dir: /source/{locale}/images/
    serve_at: /{locale}/static/images/
[/sourcecode]

### Specifying the site root

You can specify the site root in `podspec.yaml` and then reference the root in path formats elsewhere. This provides flexibility should you need to change the site root later, and allows you to avoid repeating the site root throughout multiple configurations.

[sourcecode:yaml]
# In podspec.yaml
root: /my-site/

# In a collection's _blueprint.yaml
path: /{root}/pages/{base}/
[/sourcecode]

## URLs in templates

Because you are provided with the freedom to change a serving path at any time, whenever you need to reference a URL in a template (such as in a `<link>` element for a stylesheet or `<a href>` for a link), you should always programmatically generate those URLs using a built-in template function.

In general, you should never refer to a linkable resource by its URL: you should refer to it by its internal pod path and leverage either `g.doc` or `g.static` to programmatically generate its URL. This technique provides you with flexibility to change URLs later without finding and replacing URLs in your site's code. Plus, it helps avoid broken links.

[sourcecode:html+jinja]
# The serving path for a content document.
{{g.doc('/content/pages/home.yaml').url.path}}

# The serving path for a static file.
{{g.static('/source/images/image.png').url.path}}
[/sourcecode]

## Checking routes

Use the `grow routes` command to quickly audit all of the routes that your site generates. You can use this command to avoid building the site and inspecting the generated fileset or saving and refreshing to check paths in the browser.

Grow validates your URL path configuration and raises errors upon misconfiguration. For example, Grow will raise an error if you generate the same serving path for two different resources – no two resources may share the same serving path.
