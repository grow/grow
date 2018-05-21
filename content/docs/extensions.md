---
$title: Create Extensions
$category: Extensions
$order: 5.2
---
[TOC]

Grow has a powerful extension system that enables you to extend the
functionality of Grow with extensions.

### Example Extension

As an example of a simple Grow extension see the [html min extension][html-min].

### Anatomy of an Extension

Grow extensions use hooks to bind the extension into different parts of the Grow
build and rendering process. The Grow extension extends the `BaseExtension` and
defines hooks that are extended of the Grow hooks.

<script src="https://gist-it.appspot.com/https://github.com/grow/grow-ext-html-min/blob/master/html_min/html_min.py"></script>

For an extension, the `available_hooks` define the hook classes that the
extension supports.

[html-min]: https://github.com/grow/grow-ext-html-min
