---
$title: Preprocessors
$category: Reference
$order: 8
---
# Preprocessors

[TOC]

Preprocessors let you take source files in your pod and run programs on them to do things like optimization and code generation. Grow runs preprocessors every time affected source files change, allowing you to "save and refresh" to preview your changes. Preprocessors are also run before deployment.

Grow includes the below preprocessors as built-ins with the SDK, and you'll always be free to bring your own external processing tools (such as Grunt or Gulp) to build files used by Grow sites.

## Closure Compiler

The [Closure Compiler](https://developers.google.com/closure/compiler/) preprocessor optimizes and compiles JavaScript files. Use Closure Compiler to make your site's JavaScript more efficient and to check your code.

[sourcecode:yaml]
kind: closure_compiler
compilation_level: {ADVANCED_OPTIMIZATIONS|SIMPLE_OPTIMIZATIONS|WHITESPACE_ONLY}
js_output_file: /static/js/main.min.js
closure_entry_point: foo.bar
manage_closure_dependencies: {yes|no}
only_closure_dependencies: {yes|no}
generate_exports: {yes|no}
output_wrapper: "(function() { %output% })();"
js:
- "/bower_components/closure-library/**.js"
- "/source/js/**.js"
- "!**_test.js"
externs:
- /source/js/externs.js
[/sourcecode]

### Including Closure Library

Grow does not implement any sort of package or dependency management system. If you want to use the `closure_compiler` preprocessor with Closure Library, you'll need to make Closure Library's sources available to the compiler. Instead of including Closure Library in its entirety in your Git repository, you could use a dependency management system such as Bower or Git submodules.

To install Closure Library using Bower, create a `bower.json` file and run `bower install`.

[sourcecode:json]
{
  "name": "<project name>",
  "private": true,
  "dependencies": {
    "closure-library": "git://github.com/google/closure-library.git"
  }
}
[/sourcecode]

## Sass

Use the [Sass CSS extension language](http://sass-lang.com/) to create, minify, and maintain your site's CSS files.

[sourcecode:yaml]
kind: sass
sass_dir: /source/sass/    # Where to find source Sass files.
out_dir: /static/css/      # Where to write generated CSS files.
[/sourcecode]
