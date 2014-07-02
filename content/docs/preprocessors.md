---
$title: Preprocessors
$category: Reference
$order: 8
---
# Preprocessors

[TOC]

Preprocessors let you take source files in your pod and run programs on them to do things like optimization and code generation. Grow runs preprocessors every time affected source files change, allowing you to "save and refresh" to preview your changes. Preprocessors are also run before deployment.

Grow includes the below preprocessors as built-ins with the SDK, and you'll always be free to bring your own external processing tools (such as Grunt or Gulp) to build files used by Grow sites.

## Closure Tools

### Closure Compiler

The [Closure Compiler](https://developers.google.com/closure/compiler/) preprocessor optimizes and compiles JavaScript files. Use Closure Compiler to make your site's JavaScript more efficient and to check your code.

Note that if you would like to leverage Closure Library, use the Closure Builder preprocessor instead. If you just want to minify some JavaScript, you can use the Closure Compiler preprocessor directly.

[sourcecode:yaml]
kind: closurecompiler

# SIMPLE_OPTIMIZATIONS, ADVANCED_OPTIMIZATIONS, or WHITESPACE_ONLY.
compilation_level: ADVANCED_OPTIMIZATIONS

# The file to generate.
js_output_file: /static/js/main.min.js

# The files to compile together.
js:
- /source/js/foo.js
- /source/js/bar.js

# (Optional) Wrap the output with this code.
output_wrapper: "(function() { %output% })();"

# (Optional) Externs to preserve throughout compilation.
externs:
- /source/js/externs.js
[/sourcecode]

### Closure Builder

Implements the Closure Compiler preprocessor and includes integration with Closure Library. Automatically scans roots for dependencies of inputs, and only compiles together code that is actually used by inputs.

[sourcecode:yaml]
kind: closurebuilder

# COMPILED, LIST, or SCRIPT.
output_mode: COMPILED

# The file to generate.
output_file: /static/js/main.min.js

# Source files to compile.
input:
- /source/js/main.js

# Namespaces to compile.
# (Either input or namespace must be specified. Not both.)
namespace:
- foo.bar

# Source directories (anything that provides requirements of above sources).
root:
- /source/js/
- /bower_components/closure-library/

compiler_flags:

  # SIMPLE_OPTIMIZATIONS, ADVANCED_OPTIMIZATIONS, or WHITESPACE_ONLY.
  compilation_level: ADVANCED_OPTIMIZATIONS

  # (Optional) Wrap the output with this code.
  output_wrapper: "(function() { %output% })();"

  # (Optional) Externs to preserve throughout compilation.
  externs:
  - /source/js/externs.js
[/sourcecode]

#### Including Closure Library

Grow does not implement any sort of package or dependency management system. If you want to use the `closurebuilder` preprocessor with Closure Library, you'll need to make Closure Library's sources available to the compiler. Instead of including Closure Library in its entirety in your Git repository, you could use a dependency management system such as Bower or Git submodules.

To install Closure Library using Bower, create a `bower.json` file and run `bower install`.

[sourcecode:json]
{
  "name": "Pod Name",
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
