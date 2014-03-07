---
$title: Podspec
$category: Reference
$order: 1
---
# Pod specification file (podspec)

[TOC]

Grow pods __must__ contain a file named `podspec.yaml`. The podspec contains flags and a few definitions that specify various behavior and properties of your site, such as URLs, the version of the Grow SDK compatible with the pod, and localization information.

** denotes a required field.*

## podspec.yaml

    project: john/example
    grow_version: 0.0.1

    flags:
      root_path: /
      static_dir: /media/

    static_dirs:
    - static_dir: /static/
      serve_at: /site/files/

    error_routes:
      default: /views/error.html

    content_security_policy:
      required: yes

    localization:
      root_path: /{locale}/
      languages:
      - en
      - fr
      - ja
      regions:
      - ca
      - jp
      - us

### project*

A unique identifier for this pod, formatted by `<owner's nickname>/<pod's nickname>`. Pod servers may implement features such as access control and workflow based on the project ID. Two different pods on the same server cannot have the same project ID.

    project: john/example

### grow_version*

The version of the Grow SDK that works with this pod. Allows decentralized instances of Grow to identify compatibility.

Grow uses [semantic versioning](http://semver.org/) which helps you know which versions of the Grow SDK will work with your pod. If your pod works with `1.2.3`, it will work at least up to `2.0.0`. Major versions (such as `2.x.x` from `1.x.x`) may introduce breaking changes when used with pods made for an older SDK version.

    grow_version: 0.0.1

### flags

#### root_path

If specified, *root_path* is automatically prepended to all URLs for all files built by the pod. This can be useful if you deploy multiple pods to the same domain, and would like to encapsulate each pod within a specific *root_path*. *root_path* can include the `{locale}` variable.

In other words, if you have a document whose path is `/foo/bar/` inside a pod whose *root_path* is `/about/`, the document is built to: `/about/foo/bar/`.

    root_path: /                  # The site lives in the directory root.
    root_path: /about/            # The site lives in the "/about/" top-level directory.
    root_path: /{locale}/about/   # The site lives in the "/{locale}/about/" directory.

#### static_dir

Specifies a directory that contains static files. This flag is shorthand for a full entry in the `static_dirs` configuration. Files placed in this directory should be used in conjunction with the `g.static` template tag, which returns a URL object for files in this directory.

    static_dir: /media/          # Files in /media/ will be served at /media/.

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

Grow can build error pages for various error codes. The error page renders a view, which can leverage the template variable `g.error` to gain additional information about the error. To specify a generic error page, use "default". When a pod is built and deployed to a storage provider such as Amazon S3 or Google Cloud Storage, the storage provider will be configured to use these error pages.

    default: /views/errors/default.html
    not_found: /views/errors/404.html
    unauthorized: /views/errors/401.html
    forbidden: /views/errors/403.html
    method_not_allowed: /views/errors/405.html
    bad_request: /views/errors/400.html
    im_a_teapot: /views/errors/418.html

### content_security_policy

Allows you to enforce a pod-wide [content security policy](http://www.html5rocks.com/en/tutorials/security/content-security-policy/).

#### required

Whether the content security policy is required on all HTML pages. If `yes`, HTML files without a content security policy will result in build errors.

    required: no
    required: yes

### localization

The default localization configuration for all content in the pod.

#### languages

Specify a list of languages that your site can be translated into. Strings will be extracted from content and views and made available for translation into these languages. In order to generate translated pages, the `path` field of a blueprint must contain a `{language}` token.

    languages:
    - en
    - fr
    - ja

#### regions

Content can be regionalized (that is, certain content can be made available for specific regions only – and content can change depending on the region). In order to generate regionalized pages, the `path` field of a blueprint must contain a `{region}` token.

    regions:
    - ca
    - jp
    - us

### preprocessors

A list of [preprocessors]([url('/content/docs/preprocessors.md')]). The type of preprocessor is determined by the `kind` key. The remaining keys are configuration parameters for the preprocessor.

    - kind: sass
      sass_dir: /source/sass/
      out_dir: /static/css/

### deployments

A mapping of named deployments. The deployment destination is determined by the `destination` key. The remaining keys are configuration parameters for the deployment. The `default` name can be used to specify the pod's default deployment.

    default:
      destination: gcs
      bucket: staging.example.com

    production:
      destination: gcs
      bucket: example.com
