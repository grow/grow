---
$title: Podspec
$category: Reference
$order: 1.02
---
# Podspec

Grow pods __must__ contain a file named `podspec.yaml`. The podspec contains flags and a few definitions that specify various behavior and properties of your site, such as URLs, the version of Grow compatible with the pod, and localization information.

## podspec.yaml

```yaml
title: Project title.
description: Project description.

home: /content/pages/<home>.yaml

static_dirs:
- static_dir: /static/
  serve_at: /site/files/

localization:
  root_path: /{locale}/
  default_locale: en
  locales:
  - de
  - en
  - fr
  - it
  aliases:
    en_uk: en_GB
  import_as:
    en_uk:
    - en_GB
  require_translations: false
  require_translations@env.prod: true

preprocessors:
- kind: sass
  sass_dir: /source/sass/
  out_dir: /static/css/

meta:
  key: value

sitemap:
  enabled: yes
  path: /sitemap.xml
  collections:
  - pages
  locales:
  - en
  - fr

deployments:
  default:
    destination: local
    out_dir: grow-codelab-build/
    env:
      name: prod
      host: example.com
      port: 80
      scheme: https
```
### static_dirs

A list of directories in the pod to treat as servable static files. Unlike the `static_dir` shorthand flag, this config provides additional customization and control over the source directory and the path at which the files are served.

```yaml
static_dirs:

# Equivalent to the "static_dir" shorthand flag.
- static_dir: /static/
  serve_at: /static/

# Serves files in the /static/ directory of the pod at the URL path /files/.
- static_dir: /static/
  serve_at: /files/

# Serves files in the /static/ directory of the pod at the root.
- static_dir: /static/
  serve_at: /
```

If you do not wish to use Grow's content management or templating features, you can leverage the other features of the system (such as testing, building, and deployment) by simply creating a `podspec.yaml` file and following the last above example. This can be a good way to migrate an existing site into Grow and slowly add new site sections leveraging Grow's content and templating features.

#### Fingerprints

Grow can rewrite static file paths with fingerprints.

```yaml
static_dirs:
- static_dir: /source/
  serve_at: /static/
  fingerprinted: true
```

In the above example, a file at `/source/images/file.png` would be served at `/static/images/file-<fingerprint>.png` where `<fingerprint>` is an md5 hash of the file's contents.

#### Filtering

By default grow ignores building any static files that start with a `.`. The behavior can be changed by adding a main level `filter` or selectively by adding the filter to a `static_dirs` item.

```yaml
filter:
  ignore_paths:
  - \.DS_STORE
  include_paths:
  - \.htaccess
```

The `ignore_paths` defines regex patterns for which files to ignore. The `include_paths` defines regex patterns that override the ignore patterns.

So if you want to ignore all files that start with a `.` except for `.htaccess` files you could do a filter like this (since the default is to ignore dot files you don't need a `ignore_paths`):

```yaml
filter:
  include_paths:
  - \.htaccess
```
### localization

The default localization configuration for all content in the pod.

#### default_locale

Sets the global, default locale to use for content when a locale is not explicitly. This allows you to set a global, default locale for the content throughout your site. For example, if you wanted to serve English content at *http://example.com/site/* and localized content at *http://example.com/{locale}/site/*, you would set *default_locale* to `en`.

It also allows you to use a non-English language as the source language for content (for example, when translating *from* Chinese *to* English).

```yaml
default_locale: en
```

#### locales

A list of locale identifiers that your site is available in. Language codes will be derived from the identifiers in this list and individual translation catalogs will be created for each language. The `{locale}` converter can be used in `path` configs (such as in `podspec.yaml` or in a blueprint).

```yaml
localization:
  locales:
  - en_US
  - de_DE
  - it_IT
```

#### aliases

A mapping of aliases to locale identifiers. This can be used to translate a Grow locale to a locale used by your web server, should the identifiers differ.

```yaml
localization:
  aliases:
    en_uk: en_gb
```

#### import_as

A mapping of external to internal locales, used when translations are imported. When translations are imported using `grow translations import`, Grow converts external locales to internal locales. This mapping can be useful if you are working with a translation provider that uses non-standard locales.

```yaml
localization:
  import_as:
    en_uk:
    - en_GB
```

#### require_translations

Flag for determining if the build requires all strings in use to be translated before being successful. To target a specific deployment use the `@env.<deployment name>` format.

```yaml
localization:
  require_translations: false
  require_translations@env.prod: true
```

#### groups

Categorize groups of locales together to allow for easy reference when tagging strings.

```yaml
# podspec.yaml
localization:
  groups:
    group1:
    - de
    - fr
    - it
```

```yaml
# /content/collectiion/document.yaml
foo: base
foo@locale.group1: tagged for de, fr, or it locales.
```

If there are already locales being used:

```yaml
# /content/collectiion/document.yaml
foo: base
foo@(en_US|en_UK): normal localization usage.
foo@locale.group1: tagged for de, fr, or it locales.
```

### preprocessors

A list of [preprocessors]([url('/content/docs/reference/preprocessors.md')]). The type of preprocessor is determined by the `kind` key. The remaining keys are configuration parameters for the preprocessor.

### meta

Metadata set at a level global to the pod. Metadata here is arbitrary, unstructured, and can be used by templates via `{{podspec.meta}}`. Typcal uses for metadata may be for setting analytics tracking IDs, site verification IDs, etc.

```yaml
meta:
  key: value
  google_analytics: UA-12345
```

### sitemap

Add `sitemap` to autogenerate a `sitemap.xml` file for your project.

```yaml
sitemap:
  enabled: yes
  path: "/{root}/sitemap.xml"   # Optional.
  collections:                  # Optional.
  - pages
  locales:                      # Optional.
  - en
  - fr
```

### deployments

A mapping of named deployments. The deployment destination is determined by the `destination` key. The remaining keys are configuration parameters for the deployment. The `default` name can be used to specify the pod's default deployment. An `env` can optionally be specified.

```yaml
default:
  destination: gcs
  bucket: staging.example.com

production:
  destination: gcs
  bucket: example.com
```

You can also specify the environment on a per-deployment basis. The environment properties are used in the `{{env}}` object, as well as used to derive the host, port, and scheme for the `url` properties of documents and static files. These are also used in sitemap generation.

```yaml
deployments:
  example:
    destination: local
    keep_control_dir: no
    control_dir: ./private/my-project/
    out_dir: ./www/html/
    env:
      host: example.com
      scheme: https
      port: 9000
```

### footnotes

Add `footnotes` to configure how footnotes are [generated in documents]([url('/content/docs/reference/documents.md')]#footnotes).

```yaml
footnotes:
  numeric_locales_pattern: US$
  symbols:
  - ∞
  - ●
  - ◐
  - ◕
```

The default set of symbols follows the Chicago Manual footnote style. Symbols are repeated after the initial list is exhausted. For example, the above configuration would make the fifth footnote use ∞∞ as the symbol.

By default, the DE and CA territories use numeric symbols instead of normal symbols. The `numeric_locales_pattern` configures what regex to apply to the locales to determine if it should use the numeric symbols instead of the normal symbol set. Ex: `numeric_locales_pattern: (US|CA)$` would make all the US and CA territories use the numeric symbols.

You can force all locales to use numeric symbols by using `use_numeric_symbols: True` or turn off the usage of numeric symbols by using `use_numeric_symbols: False`.
