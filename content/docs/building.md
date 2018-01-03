---
$title: Building
$category: Workflow
$order: 1
---
[TOC]

Grow implements several commands to help you build your pod to generate files and inspect the pod for ways to improve development and deployment.

## Commands

### build

Builds a pod, generating all the static files needed to render your site. By default, the `grow build` command outputs files to the `build/` directory within your pod. You can specify a target directory by using an optional fourth argument. In order to deploy your site locally or to a launch destination, [see the `grow deploy` command]([url('/content/docs/deployment.md')]).

[sourcecode:bash]
# Builds pod to "build" directory.
grow build

# Builds pod to <dir>.
grow build --out_dir=<dir>

# Builds pod and shows untranslated strings.
grow build --locate-untranslated
[/sourcecode]

When using the `--locate-untranslated` flag Grow will also output all of the untranslated strings into `.po` files in the `.grow/untranslated/` directory to make it easier to request missing translations.

### preprocess

Runs just the preprocessor step of the build process.

### inspect

#### routes

Shows all routes from your pod. Useful for testing and debugging routing.

[sourcecode:bash]
grow inspect routes
[/sourcecode]

#### untranslated

Attempts to correlate the strings that are missing translation tagging in front matter and the templates use of the `gettext` (`_(...)`) function.

[sourcecode:bash]
grow inspect untranslated
[/sourcecode]
