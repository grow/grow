---
$title: Launch destinations
$category: Workflow
$order: 2
---
# Launch destinations

[TOC]

Pods can be deployed in two ways: static and dynamic. For static deployment, a pod is built and the resulting fileset is deployed to the launch destination. For dynamic deployment, a pod is launched to a Grow PodServer, which then serves the pod up dynamically. Dynamic deployment is not yet available in the current version of Grow.

## Deployment types

- __Static__: Grow generates a static build of your website, and deploys that build to a static web server. Some web servers (such as S3 and GCS) can be autoconfigured by Grow and include features such as redirects, custom error pages, etc.
- __Dynamic (not yet available)__: Pods can be deployed to a dynamic PodServer for additional "dynamic" functionality. Dynamic functionality may include things such as forms, enforcing login, searching, etc.

## Launch process

The launch process for a pod remains the same regardless of the destination for your deployment. Here are the steps that every launch undergoes:

1. __Processing__: All pre and post-processors used by your pod are run.
1. __Pod testing:__ Built-in and pod-specific tests are run to verify your site.
1. __Destination pre-launch__: A test is run to verify that Grow can connect to and configure your destination.
1. __Deployment index comparison__: The deployment index is retrieved from the destination (if it exists), and a diff between what's live and what's about to be deployed is presented to you for confirmation.
1. __Deployment__
    1. The diff between your local index and the deployment index is applied (new files are written, old files are deleted, and edits are made).
    1. The destination is configured (if applicable) with things like redirects, custom error pages, etc.
1. __Destination post-launch__: Any clean up tasks required by the destination are run.
    1. The deployment log is updated at the destination.
    1. The local index is written to the destination.

These universal steps ensure that every deployment remains consistent – and so that future deployments have knowledge of all past deployments.

## Launch destinations

### Google Cloud Storage

### Amazon S3

### Local

### Custom destinations

### Google App Engine (coming soon)

Stub documentation for App Engine destination.

### Dropbox (coming soon)

Stub documentation for Dropbox destination.

### GitHub Pages (coming soon)

Stub documentation for GitHub destination.

## Deployment index
