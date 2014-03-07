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

### include

Includes another document's Markdown body directly. Enables the reuse of content and "partial documents". The include tag must be placed at the beginning of the line.

    [include('/content/<collection>/<document>.md')]

### url

Returns the URL to a document. Follows the "don't repeat yourself" philosophy, preventing you from having to specify URLs manually.

    [url('/content/<collection>/<document>.md')]

This extension can be used in conjunction with the standard Markdown link syntax.

    [Back to the homepage.]([url('/content/<collection>/<document>.md')])
