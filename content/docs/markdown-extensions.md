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

[sourcecode:text]
| Header 1 | Header 2
|-|-|
| Row 1 | Content
| Row 2 | Content
[/sourcecode]

### toc

Generates a table of contents based on the headings in a document. [View documentation](http://pythonhosted.org/Markdown/extensions/toc.html).

[sourcecode:text]
[​TOC]
[/sourcecode]

## Custom extensions

The following extensions are added by Grow and have been enabled.

### include

Includes content from another document.

[sourcecode:text]
# Remove the extra space after `)`.
[include('/content/shared/stuff.md') ]
[/sourcecode]

### url

Url to a document or static file in the pod.

[sourcecode:text]
# Remove the extra space after `)`.
[url('/content/pages/archive.md') ]
[/sourcecode]

### sourcecode

Implements pygments syntax highlighting for code snippets.

[sourcecode:text]
[​sourcecode:html]
<!doctype html>
<meta charset="utf-8">
<title>Hello World!</title>
<p>Source code highlighting.
[​/sourcecode]
[/sourcecode]

The sourcecode extension also supports GitHub-flavor backticks.

[sourcecode:text]
`​``javascript
console.log('Hello World');
`​``
[/sourcecode]
