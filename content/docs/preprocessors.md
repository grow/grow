---
$title: Preprocessors
$category: Reference
$order: 8
---
# Preprocessors

[TOC]

Preprocessors do things like optimization and code generation against your pod's source files. Grow runs preprocessors every time affected source files change, allowing you to "save and refresh" to preview your changes. Preprocessors are also run at build time.

Grow includes the below preprocessors as built-ins with the SDK, and you'll always be free to bring your own external processing tools (such as Grunt or Gulp).

## Closure Compiler

The [Closure Compiler](https://developers.google.com/closure/compiler/) preprocessor optimizes and compiles JavaScript files. Use Closure Compiler to make your site's JavaScript more efficient and to check your code.

[sourcecode:yaml]
kind: closure_compiler
angular_pass: {yes|no}
compilation_level: {ADVANCED_OPTIMIZATIONS|SIMPLE_OPTIMIZATIONS|WHITESPACE_ONLY}
generate_exports: {yes|no}
manage_closure_dependencies: {yes|no}
only_closure_dependencies: {yes|no}
output_wrapper: "(function() { %output% })();"
js_output_file: /static/js/main.min.js
closure_entry_point:
- foo.main
- bar.main
js:
- "/bower_components/closure-library/**.js"
- "/source/js/**.js"
- "!**_test.js"
externs:
- /source/js/externs.js
[/sourcecode]

### Including Closure Library

Grow does not implement any sort of package or dependency management system. If you want to use the Closure Compiler preprocessor with Closure Library, you'll need to make Closure Library's sources available to the compiler. Instead of including Closure Library in its entirety in your Git repository, you could use a dependency management system such as Bower or Git submodules.

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

## Google Sheets

The Google Sheets preprocessor downloads data from a Google Sheet and saves it to a data file within your pod. The data can then be consumed by the `g.csv` tag, for example, in templates.

After enabling this preprocessor, when you run the `grow build` command, you will be prompted (once on the command line) to authorize Grow to read your Google Drive files.

Grow will export data from Google Sheets as either JSON or CSV, depending on the extension used in the `path` field.

[sourcecode:yaml]
kind: google_sheets
path: /data/filename.{csv|json}                       # Where to save downloaded file.
id: 1ZhJshmT2pZq_IALA6leXJ0oRuKVO12N9BbjAarAT8kI      # Spreadsheet ID.
gid: 0                                                # Worksheet ID (optional).
[/sourcecode]

## Sass

Use the [Sass CSS extension language](http://sass-lang.com/) to create, minify, and maintain your site's CSS files. Sass files in `sass_dir` must have either a `.scss` or `.sass` extension and are automatically generated to files ending in `.min.css`.

[sourcecode:yaml]
kind: sass
sass_dir: /source/sass/         # Where to find source Sass files.
out_dir: /static/css/           # Where to write generated CSS files.
suffix: .min.css                # Suffix of the generated filename (optional).
# Style of compiled result (optional, default: compressed).
output_style: {nested|expanded|compact|compressed}
source_comments: {yes|no}       # Whether to add comments about source lines (optional).
image_path: /static/images/     # Where to find images (optional).
[/sourcecode]
