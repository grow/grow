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

    home: /content/pages/<home>.yaml
    root: /url/path/to/site/root/

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

    deployments:
      default:
        destination: local
        out_dir: grow-codelab-build/

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

### deployments

A mapping of named deployments. The deployment destination is determined by the `destination` key. The remaining keys are configuration parameters for the deployment. The `default` name can be used to specify the pod's default deployment.

[sourcecode:yaml]
default:
  destination: gcs
  bucket: staging.example.com

production:
  destination: gcs
  bucket: example.com
[/sourcecode]
