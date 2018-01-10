---
$title: Markdown reference
$category: Reference
$order: 5.1
---
[TOC]

Grow uses the [Python-Markdown](https://github.com/waylan/Python-Markdown) package for its Markdown implementation. You can see [John Gruber's Syntax Documentation](http://daringfireball.net/projects/markdown/syntax) to learn about Markdown's default syntax rules.

## Default extensions

These built-in extensions are enabled by default.

### tables

Generates tables. [View documentation](http://pythonhosted.org/Markdown/extensions/tables.html).

```
| Header 1 | Header 2
|-|-|
| Row 1 | Content
| Row 2 | Content
```

### toc

Generates a table of contents based on the headings in a document. [View documentation](http://pythonhosted.org/Markdown/extensions/toc.html).

```
[​TOC]
```

## Custom extensions

The following extensions are added by Grow and have been enabled.

### include

Includes content from another document.

```
# Remove the extra space after `)`.
[include('/content/shared/stuff.md') ]
```

### url

Url to a document or static file in the pod.

```
# Remove the extra space after `)`.
[url('/content/pages/archive.md') ]
```

### sourcecode

Implements pygments syntax highlighting for code snippets.

```
[​sourcecode:html]
<!doctype html>
<meta charset="utf-8">
<title>Hello World!</title>
<p>Source code highlighting.
[​/sourcecode]
```

The sourcecode extension also supports GitHub-flavor backticks.

```
`​``javascript
console.log('Hello World');
`​``
```
