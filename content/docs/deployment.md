---
$title: Launch destinations
$category: Workflow
---
# Launch destinations

Pods can be deployed in two ways: static and dynamic. For static deployment, a pod is built and the resulting fileset is deployed to the launch destination. For dynamic deployment, a pod is launched to a Grow PodServer, which then serves the pod up dynamically. Dynamic deployment is not yet available in the current version of Grow.

## Launch destinations

- Amazon S3
- Google Cloud Storage
- Local filesystem

### Deployment types

- __Static__: Grow generates a static build of your website, and deploys that build to a static web server. Some web servers (such as S3 and GCS) can be autoconfigured by Grow and include features such as redirects, custom error pages, etc.
- __Dynamic (not yet available)__: Pods can be deployed to a dynamic PodServer for additional "dynamic" functionality. Dynamic functionality may include things such as forms, enforcing login, searching, etc.

## Launch process

## Deployment index
