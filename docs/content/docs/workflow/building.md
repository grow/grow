---
$title: Developing & building
$category: Workflow
$order: 10.2
---
# Developing & building

Grow provides a built-in local development server for instant previews and a static builder that compiles your pod into plain HTML, CSS, JS, and assets.

## Local development server

Start the development server from your pod directory (or pass the path to a pod):

```bash
grow run
```

Grow serves your site locally at `http://localhost:8080/` and includes a built-in **Dev Console** at `http://localhost:8080/_grow/` where you can inspect routes, patterns, localized URLs, and pod metadata.

Edits to content (`content/`), templates (`views/`), static files, or `podspec.yaml` are picked up automatically on refresh.

```bash
# Run on a specific port or pod directory
grow run --port=8081 ./my-site
```

## Building static output

Use `grow build` to render every route in your pod to static files. By default, files are written to `./build/` inside the pod directory.

```bash
# Build the current pod to ./build/
grow build

# Build to a custom output directory
grow build --out_dir=./dist

# Build and report any untranslated strings
grow build --locate-untranslated
```

When `--locate-untranslated` is passed, Grow exports missing strings to `.po` files in `.grow/untranslated/` so they can be sent for translation.

## Preprocessors

To run configured preprocessors without running a full build:

```bash
grow preprocess
```

## Inspecting a pod

Grow includes inspection commands for debugging routes and localization coverage:

```bash
# Print every resolved URL route in the pod
grow inspect routes

# Find strings missing translation tagging in templates and front matter
grow inspect untranslated
```
