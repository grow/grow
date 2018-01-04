---
$title: Build Environments
$category: Reference
$order: 5
---
[TOC]

Environment information is defined in the [podspec]([url('/content/docs/podspec.md')]#deployments).
Most grow commands default to use the development environment. Some grow commands allow for specifying an environment to use
by using the `--deployment` flag. This allows you to do things like test builds with the environment settings from production.

## Front matter tagging

You can tag front matter data based on the environment information.

[sourcecode:yaml]
title@: Title
title@env.prod: Title in production
title@env.staging: Title in staging
[/sourcecode]

[sourcecode:text]
# Default
{{doc.title}} -> Title

# Prod Environment
{{doc.title}} -> Title in production

# Staging Environment
{{doc.title}} -> Title in staging
[/sourcecode]

This can also be helpful for preventing specific pages from being deployed to specific deployments.

[sourcecode:yaml]
$path: /styleguide/
$path@env.prod: ""
[/sourcecode]
