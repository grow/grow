---
$title: Preprocessors
$category: Reference
$order: 8
---
# Preprocessors

[TOC]

Preprocessors do things like optimization and code generation against your pod's source files. Grow runs preprocessors every time affected source files change, allowing you to "save and refresh" to preview your changes. Preprocessors are also run at build time.

Grow includes the below preprocessors as built-ins with the SDK, and you'll always be free to bring your own external processing tools (such as Grunt or Gulp).

## Global settings

By default, preprocessors run when the development server is started and when your site is built. You can control preprocessor execution by using the `autorun` parameter and optionally by using the `name` parameter.

[sourcecode:yaml]
preprocessors:
- name: my_preprocessor
  autorun: false
[/sourcecode]

A preprocessor with the above configuration will only be run when using `grow preprocess -A` or when using `grow preprocess -p my_preprocessor`. This can be handy to control how often a data-importing preprocessor (such as Google Sheets or Google Docs importers) run. You may not want to run those preprocessors each time your site is built.

## Kinds

### Google Sheets

The Google Sheets preprocessor downloads data from a Google Sheet and saves it to a data file within your pod. The data can then be consumed by the `g.csv` tag, for example, in templates.

After enabling this preprocessor, when you run the `grow build` command, you will be prompted (once on the command line) to authorize Grow to read your Google Drive files.

Grow will export data from Google Sheets as either JSON or CSV, depending on the extension used in the `path` field.

[sourcecode:yaml]
preprocessors:
- kind: google_sheets
  path: /data/filename.{csv|json}                       # Where to save downloaded file.
  id: 1ZhJshmT2pZq_IALA6leXJ0oRuKVO12N9BbjAarAT8kI      # Spreadsheet ID.
  gid: 0                                                # Worksheet ID (optional).
[/sourcecode]

### Sass

Use the [Sass CSS extension language](http://sass-lang.com/) to create, minify, and maintain your site's CSS files. Sass files in `sass_dir` must have either a `.scss` or `.sass` extension and are automatically generated to files ending in `.min.css`.

[sourcecode:yaml]
kind: sass
preprocessors:
- sass_dir: /source/sass/         # Where to find source Sass files.
  out_dir: /static/css/           # Where to write generated CSS files.
  suffix: .min.css                # Suffix of the generated filename (optional).
  # Style of compiled result (optional, default: compressed).
  output_style: {nested|expanded|compact|compressed}
  source_comments: {yes|no}       # Whether to add comments about source lines (optional).
  image_path: /static/images/     # Where to find images (optional).
[/sourcecode]
