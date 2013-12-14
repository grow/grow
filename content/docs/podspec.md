---
$title: Podspec
$category: Reference
$order: 0
---
# Pod specification file (podspec)

Grow pods __must__ contain a file named `podspec.yaml`. The podspec contains flags and a few definitions that specify various behavior and properties of your site, such as URLs, the version of the Grow SDK compatible with the pod, and localization information.

** denotes a required field.*

## podspec.yaml

    project: john/example
    grow_version: 0.0.1

    flags:
      static_dir: /media/

    locales:
      default:
        languages:
        - en
        - fr
        - ja
        regions:
        - ca
        - jp
        - us

### project*

A unique identifier for this pod, formatted with `<owner's nickname>/<pod's nickname>`. Pod servers may implement features such as access control and workflow based on the project ID. Two pods on the same server cannot have the same project ID.

    project: john/example

### grow_version*

The version of the Grow SDK that works with this pod. Allows decentralized instances of Grow to identify compatibility.

Grow uses [semantic versioning](http://semver.org/) which helps you know which versions of the Grow SDK will work with your pod. If your pod works with `1.2.3`, it will work at least up to `2.0.0`. Major versions (such as `2.x.x` from `1.x.x`) may introduce breaking changes when used with pods made for an older SDK version.

    grow_version: 0.0.1

### flags

#### static_dir

Specifies a directory that contains static files. Files placed in this directory should be used in conjunction with the `g.static` template tag, which returns a URL path that serves static files in this directory.

    static_dir: /media/

### locales

Locales are organized into groups containing languages and regions. Currently, Grow supports one exactly locale group, __default__.

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
