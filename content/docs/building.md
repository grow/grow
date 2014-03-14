---
$title: Building and testing
$category: Workflow
$order: 0
---
# Building your site

[TOC]

The Grow SDK implements several commands to help you build and test your pod and its generated files.

## Commands

### dump

Builds your pod and dumps generated files to a local destination using the `grow dump` command. This command does nothing special in terms of deployment management or timing. In order to deploy your site locally or to a launch destination, [see the `grow deploy` command]([url('/content/docs/deployment.md')]).

    # Dumps <pod> to directory <out directory>.
    grow dump <pod> <out directory>

### routes

Shows all routes built by your pod. Useful for testing and debugging.

    grow routes <pod>
