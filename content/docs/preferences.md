---
$title: Command Preferences
$category: Reference
$order: 1.13
---
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

```yaml
grow:
  build:
    deployment: null
    preprocess: true
    clear-cache: false
    locate-untranslated: false
    re-route: false
```

### Deploy

```yaml
grow:
  deploy:
    preprocess: true
    confirm: true
    test: true
    force-untranslated: false
```

### Extract

```yaml
grow:
  extract:
    include-obsolete: null
    localized: null
    include-header: null
    fuzzy-matching: null
```

### Filter

```yaml
grow:
  filter:
    include-obsolete: false
    localized: false
    include-header: false
    out-dir: null
    force: false
```

### Import Translations

```yaml
grow:
  translations:
    import:
      include-obsolete: true
```

### Preprocess

```yaml
grow:
  preprocess:
    deployment: null
```

### Run

```yaml
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
```

### Stage

```yaml
grow:
  stage:
    preprocess: true
    force-untranslated: false
```

### Stats

```yaml
grow:
  stats:
    full: true
```

### Upload Translations

```yaml
grow:
  translations:
    upload:
      download: true
      extract: true
      force: false
```

## Shared Command Flag Defaults

Some of the flags are common between different Grow commands. These can be done as custom defaults in each command or in the shared settings:

```yaml
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
```
