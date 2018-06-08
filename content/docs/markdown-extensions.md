---
$title: Markdown reference
$category: Reference
$order: 1.09
---
[TOC]

Grow uses the [Python-Markdown](https://github.com/waylan/Python-Markdown) package for its Markdown implementation. You can see [John Gruber's Syntax Documentation](http://daringfireball.net/projects/markdown/syntax) to learn about Markdown's default syntax rules.

These built-in extensions are enabled by default.

## Tables

Generates tables. [View documentation](http://pythonhosted.org/Markdown/extensions/tables.html).

```md
| Header 1 | Header 2
|-|-|
| Row 1 | Content
| Row 2 | Content
```

## Table of Contents

Generates a table of contents based on the headings in a document. [View documentation](https://python-markdown.github.io/extensions/toc/).

```md
[​TOC]
```

### Configuration

Configuration options available to the [toc extension](https://python-markdown.github.io/extensions/toc/#usage) can be configured in the podspec.

```yaml
# podspec.yaml
markdown:
  extensions:
  - kind: toc
    marker: [TOC]
    title:
    baselevel: 1
    anchorlink: False
    permalink: False
    separator: "-"
```

## Include

Includes content from another document.

```md
# Remove the extra space after `)`.
[include('/content/shared/stuff.md') ]
```

## URL

Url to a document or static file in the pod.

```md
# Remove the extra space after `)`.
[url('/content/pages/archive.md') ]
```

## Sourcecode

Implements pygments syntax highlighting for code snippets.

```md
[​sourcecode:html]
<!doctype html>
<meta charset="utf-8">
<title>Hello World!</title>
<p>Source code highlighting.
[​/sourcecode]
```

You can also highlight specific lines:

```md
[​sourcecode:html, hl_lines="1 3"]
<!doctype html>
<meta charset="utf-8">
<title>Hello World!</title>
<p>Source code highlighting.
[​/sourcecode]
```

Which appears as:

​[sourcecode:html, hl_lines="1 3"]
<!doctype html>
<meta charset="utf-8">
<title>Hello World!</title>
<p>Source code highlighting.
[/sourcecode]

### Configuration

```yaml
# podspec.yaml
markdown:
  extensions:
  - kind: sourcecode
    classes: False         # Uses classes instead of inline styles.
    class_name: code       # Class to use on the wrapper div.
    highlighter: pygments  # pygments/plain
    theme: default         # Pygments theme name.
```

If you choose to use classes instead of inline styles you can use pygments to generate the stylesheet for a [theme](http://richleland.github.io/pygments-css/).

To generate the styles for the `friendly` theme with a `code` class wrapper.

```bash
pygmentize -S friendly -f html -a .code > styles.css
```

## Code Block
An alternative to the `[sourcecode]` block is to use GitHub-flavor backticks via python markdown's [code fence extension](https://python-markdown.github.io/extensions/fenced_code_blocks/).

```md
`​``js
console.log('Hello World');
`​``
```

You can also highlight specific lines:

```md
`​``js hl_lines="1"
console.log('Hello World');
`​``
```

Which would show up as:

```js hl_lines="1"
console.log('Hello World');
```

### Configuration

```yaml
# podspec.yaml
markdown:
  extensions:
  - kind: markdown.extensions.codehilite
    classes: False         # Uses classes instead of inline styles.
    class_name: code       # Class to use on the wrapper div.
    highlighter: pygments  # pygments/plain
    theme: default         # Pygments theme name.
```

If you choose to use classes instead of inline styles you can use pygments to generate the stylesheet for a [theme](http://richleland.github.io/pygments-css/).

To generate the styles for the `friendly` theme with a `code` class wrapper.

```bash
pygmentize -S friendly -f html -a .code > styles.css
```
