---
$title: Themes & samples
$slug: samples
$category: Get started
$order: 0.1
---
# Themes & samples

## Getting samples

The `grow init` command accepts either a theme name (for themes owned by the [growthemes organization on GitHub](http://github.com/growthemes)) or the URL to a git repo containing the theme.

```bash
# Clones the codelab site to a directory "./foo".
grow init codelab ./foo

# Clones Grow.io site to a directory "./grow.io".
grow init https://github.com/grow/grow.io grow.io
```

## Themes

You can use the `grow init <theme> <dir>` command to clone any of the below themes to your system.

- [base](https://github.com/growthemes/base) – a minimal Grow site, recommended
- [cards](https://github.com/growthemes/cards)
- [codelab](https://github.com/growthemes/codelab)
- [product](https://github.com/growthemes/product)
- [scaffold](https://github.com/growthemes/scaffold)

To contribute to themes on the `grow init` command, send pull requests to GitHub.

## Other samples

- [grow.io](https://github.com/grow/grow.io) – This documentation site!
- [Test data](https://github.com/grow/grow/tree/master/grow/pods/testdata/pod) – Pod used by Grow's unit tests (note: you cannot clone this using `grow init`).
