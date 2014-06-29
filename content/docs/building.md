---
$title: Building and testing
$category: Workflow
$order: 0
---
# Building your site

[TOC]

The Grow SDK implements several commands to help you build and test your pod and its generated files.

## Commands

### build

Builds a pod, generating all the static files needed to render your site. By default, the `grow build` command outputs files to the `build` directory within your pod. You can specify a target directory by using an optional fourth argument. In order to deploy your site locally or to a launch destination, [see the `grow deploy` command]([url('/content/docs/deployment.md')]).

[sourcecode:bash]
# Builds pod to "build" directory.
grow build <pod>

# Builds pod to <dir>.
grow build <pod> <dir>
[/sourcecode]

### routes

Shows all routes built by your pod. Useful for testing and debugging.

[sourcecode:bash]
grow routes <pod>
[/sourcecode]
