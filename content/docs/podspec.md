---
$title: Podspec
$category: Reference
$order: 1
---
# Pod specification file (podspec)

[TOC]

Grow pods __must__ contain a file named `podspec.yaml`. The podspec contains flags and a few definitions that specify various behavior and properties of your site, such as URLs, the version of the Grow SDK compatible with the pod, and localization information.

## podspec.yaml

    grow_version: ">=0.0.1"
    title: Project title.
    description: Project description.

    home: /content/pages/<home>.yamls
    static_dirs:
    - static_dir: /static/
      serve_at: /site/files/

    error_routes:
      default: /views/error.html

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

### grow_version

The version of the Grow SDK that works with this pod. Grow displays a warning if the version of the SDK does not match this specification in `podspec.yaml`.

Grow uses [semantic versioning](http://semver.org/) which helps you know which versions of the Grow SDK will work with your pod. If your pod works with `1.2.3`, it will work at least up to `2.0.0`. Major versions (such as `2.x.x` from `1.x.x`) may introduce breaking changes when used with pods made for an older SDK version.

This value must be a semantic version *specification*.

    grow_version: ">=0.0.1"       # At least SDK version 0.0.1.

### static_dirs

A list of directories in the pod to treat as servable static files. Unlike the `static_dir` shorthand flag, this config provides additional customization and control over the source directory and the path at which the files are served.

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

If you do not wish to use Grow's content management or templating features, you can leverage the other features of the system (such as testing, building, and deployment) by simply creating a `podspec.yaml` file and following the last above example. This can be a good way to migrate an existing site into Grow and slowly add new site sections leveraging Grow's content and templating features.

#### Fingerprints

Grow can rewrite static file paths with fingerprints.

    static_dirs:
    - static_dir: /source/
      serve_at: /static/
      fingerprinted: true

In the above example, a file at `/source/images/file.png` would be served at `/static/images/file-<fingerprint>.png` where `<fingerprint>` is an md5 hash of the file's contents.

### error_routes

Grow can build error pages for various error codes. The error page renders a view, which can leverage the template variable `{{error}}` to gain additional information about the error. To specify a generic error page, use "default". When a pod is built and deployed to a storage provider such as Amazon S3 or Google Cloud Storage, the storage provider will be configured to use these error pages.

    default: /views/errors/default.html
    not_found: /views/errors/404.html
    unauthorized: /views/errors/401.html
    forbidden: /views/errors/403.html
    method_not_allowed: /views/errors/405.html
    bad_request: /views/errors/400.html
    im_a_teapot: /views/errors/418.html

### localization

The default localization configuration for all content in the pod.

#### default_locale

Sets the global, default locale to use for content when a locale is not explicitly. This allows you to set a global, default locale for the content throughout your site. For example, if you wanted to serve English content at *http://example.com/site/* and localized content at *http://example.com/{locale}/site/*, you would set *default_locale* to `en`.

It also allows you to use a non-English language as the source language for content (for example, when translating *from* Chinese *to* English).

    default_locale: en

#### locales

A list of locale identifiers that your site is available in. Language codes will be derived from the identifiers in this list and individual translation catalogs will be created for each language. The `{locale}` converter can be used in `path` configs (such as in `podspec.yaml` or in a blueprint).

[sourcecode:yaml]
locales:
- en_US
- de_DE
- it_IT
[/sourcecode]

#### aliases

A mapping of aliases to locale identifiers. This can be used to translate a Grow locale to a locale used by your web server, should the identifiers differ.

[sourcecode:yaml]
aliases:
  en_uk: en_gb
[/sourcecode]

#### import_as

A mapping of external to internal locales, used when translations are imported. When translations are imported using `grow import_translations`, Grow converts external locales to internal locales. This mapping can be useful if you are working with a translation provider that uses non-standard locales.

[sourcecode:yaml]
import_as:
  en_uk:
  - en_GB
[/sourcecode]

### preprocessors

A list of [preprocessors]([url('/content/docs/preprocessors.md')]). The type of preprocessor is determined by the `kind` key. The remaining keys are configuration parameters for the preprocessor.

[sourcecode:yaml]
kind: sass
sass_dir: /source/sass/
out_dir: /static/css/
[/sourcecode]

### meta

Metadata set at a level global to the pod. Metadata here is arbitrary, unstructured, and can be used by templates via `{{podspec.meta}}`. Typcal uses for metadata may be for setting analytics tracking IDs, site verification IDs, etc.

[sourcecode:yaml]
meta:
  key: value
  google_analytics: UA-12345
[/sourcecode]

### sitemap

Add `sitemap` to autogenerate a `sitemap.xml` file for your project.

[sourcecode:yaml]
sitemap:
  enabled: yes
  path: "/{root}/sitemap.xml"   # Optional.
  collections:                  # Optional.
  - pages
  locales:                      # Optional.
  - en
  - fr
[/sourcecode]

### deployments

A mapping of named deployments. The deployment destination is determined by the `destination` key. The remaining keys are configuration parameters for the deployment. The `default` name can be used to specify the pod's default deployment. An `env` can optionally be specified.

[sourcecode:yaml]
default:
  destination: gcs
  bucket: staging.example.com

production:
  destination: gcs
  bucket: example.com
[/sourcecode]

You can also specify the environment on a per-deployment basis. The environment properties are used in the `{{env}}` object, as well as used to derive the host, port, and scheme for the `url` properties of documents and static files. These are also used in sitemap generation.

[sourcecode:yaml]
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
[/sourcecode]

For each deployment you can also set the option to prevent deploying when there are untranslated strings found during the deployment.

<div class="badge badge-docs-incomplete">The configuration for blocking untranslated strings will be changing in the next release of Grow. Feel free to try out the feature, but your config will need to be updated once Grow is past version 0.2.2.</div>

[sourcecode:yaml]
deployments:
  production:
    base_config:
      prevent_untranslated: true
[/sourcecode]

### footnotes

Add `footnotes` to configure how footnotes are [generated in documents]([url('/content/docs/documents.md')]#footnotes).

[sourcecode:yaml]
footnotes:
  numeric_locales_pattern: US$
  symbols:
  - ∞
  - ●
  - ◐
  - ◕
[/sourcecode]

The default set of symbols follows the Chicago Manual footnote style. Symbols are repeated after the initial list is exhausted. For example, the above configuration would make the fifth footnote use ∞∞ as the symbol.

By default, the DE and CA territories use numeric symbols instead of normal symbols. The `numeric_locales_pattern` configures what regex to apply to the locales to determine if it should use the numeric symbols instead of the normal symbol set. Ex: `numeric_locales_pattern: (US|CA)$` would make all the US and CA territories use the numeric symbols.

You can force all locales to use numeric symbols by using `use_numeric_symbols: True` or turn off the usage of numeric symbols by using `use_numeric_symbols: False`.
