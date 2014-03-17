---
$title: Themes & samples
$slug: samples
$category: Get Started
$order: 3
---
# Themes and samples

[TOC]

An actual directory of samples is coming soon. In the meantime, you can view the below GitHub projects, which are all actual pods or themes.

## Getting samples

The `grow init` command accepts either a theme name (for themes owned by the [growthemes organization on GitHub](http://github.com/growthemes)) or the URL to a git repo containing the theme.

    # Clones the codelab theme to a directory "./foo".
    grow init codelab ./foo

    # Clones the growsdk.org pod to a directory "./growsdk.org".
    grow init https://github.com/grow/growsdk.org growsdk.org

## Themes

You can use the `grow init <theme> <dir>` command to clone any of the below themes to your system.

__* indicates not implemented__

- [blank](https://github.com/growthemes/blank) *
- [blog](https://github.com/growthemes/blog) *
- [cards](https://github.com/growthemes/cards)
- [codelab](https://github.com/growthemes/codelab)
- [landing](https://github.com/growthemes/blog) *

Want to contribute a theme to the `grow init` command? Send a pull request to growthemes on GitHub!

## Samples

- [growsdk.org](https://github.com/grow/growsdk.org) – This documentation site!
- [Test data](https://github.com/grow/pygrow/tree/master/grow/pods/testdata/pod) – Pod used by the Grow SDK's unit tests (note: you cannot clone this using `grow init`).
