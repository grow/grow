---
$title: Preprocessors
$category: Reference
$order: 8
---
# Preprocessors

[TOC]

Preprocessors let you take source files in your pod and run programs on them to do things like optimization and code generation. Grow runs preprocessors every time affected source files change, allowing you to "save and refresh" to preview your changes. Preprocessors are also run upon deployment.

## Closure Compiler

The [Closure Compiler](https://developers.google.com/closure/compiler/) preprocessor optimizes and compiles JavaScript files. Use Closure Compiler to make your site's JavaScript more efficient and to check your code. The Closure Compiler preprocessor watches your pod's JavaScript files for changes and compiles them on the fly.

    - kind: closure-compiler

## Sass

The [Sass](http://sass-lang.com/) preprocessor lets you use the Sass CSS extension language to create and maintain your site's CSS files. The Sass preprocessor watches your pod's Sass files for changes, and compiles them on the fly.

    - kind: sass
      sass_dir: /source/sass/    # Where to find source Sass files.
      out_dir: /static/css/      # Where to write generated CSS files.
