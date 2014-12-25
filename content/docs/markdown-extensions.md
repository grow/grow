---
$title: Markdown reference
$category: Reference
$order: 5.1
---
# Markdown reference

[TOC]

The Grow SDK uses the [Python-Markdown](https://github.com/waylan/Python-Markdown) package for its Markdown implementation. You can see [John Gruber's Syntax Documentation](http://daringfireball.net/projects/markdown/syntax) to learn about Markdown's default syntax rules.

## Default extensions

The following built-in extensions are enabled by default:

- [tables](http://pythonhosted.org/Markdown/extensions/tables.html)
- [toc](http://pythonhosted.org/Markdown/extensions/toc.html)

## Custom extensions

The following extensions are specific to Grow and are available for you to use.

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
