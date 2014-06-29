---
$title: Preprocessors
$category: Reference
$order: 8
---
# Preprocessors

[TOC]

Preprocessors let you take source files in your pod and run programs on them to do things like optimization and code generation. Grow runs preprocessors every time affected source files change, allowing you to "save and refresh" to preview your changes. Preprocessors are also run upon deployment.

Grow includes the below preprocessors built-in to the SDK, and you'll always be free to bring your own external processing tools to build files used by Grow sites.

## Closure Builder

Implements the Closure Compiler preprocessor but provides integration with Closure Library.

[sourcecode:yaml]
kind: closurebuilder
output_mode: COMPILED
output_file: /static/js/main.min.js
root:
- /source/js/
- /ext/closure-library/
input:
- /source/js/main.js
compiler_flags:
  output_wrapper: "(function() { %output% })();"
  compilation_level: ADVANCED_OPTIMIZATIONS
[/sourcecode]

## Closure Compiler

The [Closure Compiler](https://developers.google.com/closure/compiler/) preprocessor optimizes and compiles JavaScript files. Use Closure Compiler to make your site's JavaScript more efficient and to check your code. The Closure Compiler preprocessor watches your pod's JavaScript files for changes and compiles them on the fly.

[sourcecode:yaml]
kind: closurecompiler
output_wrapper: "(function() { %output% })();"
compilation_level: ADVANCED_OPTIMIZATIONS
[/sourcecode]

## Sass

The [Sass](http://sass-lang.com/) preprocessor lets you use the Sass CSS extension language to create and maintain your site's CSS files. The Sass preprocessor watches your pod's Sass files for changes, and compiles them on the fly.

[sourcecode:yaml]
kind: sass
sass_dir: /source/sass/    # Where to find source Sass files.
out_dir: /static/css/      # Where to write generated CSS files.
[/sourcecode]
