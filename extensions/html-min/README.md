# HTML Min Extension (`grow-ext-html-min`)

Minifies rendered HTML documents in Grow sites using Python's standard library
(`html.parser`), with zero external third-party dependencies.

## Installation

Add to `extensions.txt`:

```text
git+https://github.com/grow/grow.git#subdirectory=extensions/html-min
```

Configure in `podspec.yaml`:

```yaml
extensions:
  post_render:
  - extensions.html_min.HtmlMinExtension:
      enabled: true
      options:
        remove_comments: true
        remove_empty_space: true
```
