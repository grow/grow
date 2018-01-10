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

```md
| Header 1 | Header 2
|-|-|
| Row 1 | Content
| Row 2 | Content
```

### toc

Generates a table of contents based on the headings in a document. [View documentation](http://pythonhosted.org/Markdown/extensions/toc.html).

```md
[​TOC]
```

## Custom extensions

The following extensions are added by Grow and have been enabled.

### include

Includes content from another document.

```md
# Remove the extra space after `)`.
[include('/content/shared/stuff.md') ]
```

### url

Url to a document or static file in the pod.

```md
# Remove the extra space after `)`.
[url('/content/pages/archive.md') ]
```

### sourcecode

Implements pygments syntax highlighting for code snippets.

```md
[​sourcecode:html]
<!doctype html>
<meta charset="utf-8">
<title>Hello World!</title>
<p>Source code highlighting.
[​/sourcecode]
```

The sourcecode extension also supports GitHub-flavor backticks using python markdown's codehilite extension.

```md
`​``js
console.log('Hello World');
`​``
```

To style the formatted code blocks you can use the pygments tool for generating themes. For example, to generate the default styles:

```bash
pygmentize -S default -f html -a .codehilite > styles.css
```

The codehilite extension can also be used to highlight specific lines:

```md
`​``js hl_lines="1"
console.log('Hello World');
`​``
```

Which would show up as:

```js hl_lines="1"
console.log('Hello World');
```
