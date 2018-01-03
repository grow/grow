---
$title: Command Preferences
$category: Reference
$order: 11
---
# Grow Preferences

[TOC]

## RC File

Grow uses a `~/.growrc.yaml` file to keep track of global Grow preferences. This file tracks:

- Auto-update preferences.
- Timestamp of the last update check.
- Custom `grow` command flag defaults.

Additionally, Grow will look for a `.growrc.yaml` file in the directory that the `grow` command is run. This allows for setting custom Grow preferences for individual projects.

## Custom Grow Command Flag Defaults

For certain command line flags you can provide custom defaults for Grow by adding them to the `.growrc.yaml` file.

### Build

[sourcecode:yaml]
grow:
  build:
    deployment: null
    preprocess: true
    clear-cache: false
    locate-untranslated: false
    re-route: false
[/sourcecode]

### Deploy

[sourcecode:yaml]
grow:
  deploy:
    preprocess: true
    confirm: true
    test: true
    force-untranslated: false
[/sourcecode]

### Extract

[sourcecode:yaml]
grow:
  extract:
    include-obsolete: null
    localized: null
    include-header: null
    fuzzy-matching: null
[/sourcecode]

### Filter

[sourcecode:yaml]
grow:
  filter:
    include-obsolete: false
    localized: false
    include-header: false
    out-dir: null
    force: false
[/sourcecode]

### Import Translations

[sourcecode:yaml]
grow:
  translations:
    import:
      include-obsolete: true
[/sourcecode]

### Preprocess

[sourcecode:yaml]
grow:
  preprocess:
    deployment: null
[/sourcecode]

### Run

[sourcecode:yaml]
grow:
  run:
    deployment: null
    host: localhost
    port: 8080
    https: false
    debug: false
    browser: false
    update-check: true
    preprocess: true
    ui: true
    re-route: false
[/sourcecode]

### Stage

[sourcecode:yaml]
grow:
  stage:
    preprocess: true
    force-untranslated: false
[/sourcecode]

### Stats

[sourcecode:yaml]
grow:
  stats:
    full: true
[/sourcecode]

### Upload Translations

[sourcecode:yaml]
grow:
  translations:
    upload:
      download: true
      extract: true
      force: false
[/sourcecode]

## Shared Command Flag Defaults

Some of the flags are common between different Grow commands. These can be done as custom defaults in each command or in the shared settings:

[sourcecode:yaml]
grow:
  shared:
    deployment: null
    force-untranslated: false
    include-header: false
    include-obsolete: false
    localized: false
    out-dir: null
    preprocess: true
    re-route: false
[/sourcecode]
