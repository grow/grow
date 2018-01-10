---
$title: Continuous integration
$category: Workflow
$order: 3
---
[TOC]

You can easily test, build, and/or deploy your website using a continuous integration (CI) system. CI systems remove extra steps from your project's lifecycle and allow you to save time on repetitive tasks.

The combination of GitHub, CI, Grow, and a static hosting service such as Google Cloud Storage or Amazon S3 allow you and your team to collaborate on Git and keep your site automatically up to date – without ever having to run a deploy command.

In fact, this is [exactly how this documentation is deployed](https://github.com/grow/grow.io/blob/master/.circleci/config.yml).

For security, when doing deployments from CI the CI providers allow you to set environment variables in the UI that can be used in the build but not committed to the repository. Your build steps can make use of these environment variables to authenticate to external services such as Google Cloud Storage or Amazon S3 when deploying.

## Using Circle CI for automatic deploys

Circle CI 2.0 makes use of docker images which can produce faster builds. Grow has a docker image ([grow/base](https://hub.docker.com/r/grow/base/)) that comes preloaded with grow and some of the common utilities used to build grow sites (like `npm` and `gcloud`).

1. Set up your deployment (both the host and the configuration in `podspec.yaml`)
1. Connect your GitHub repo with Circle CI
1. Configure Circle CI

To configure Circle CI, add a `.circleci/config.yml` file in your repository's root. Any required access keys can be configured as secure environment variables in the _settings_ section of your Circle CI project.

<script src="https://gist.github.com/Zoramite/d446ebb996f95e93003ebfde397848c0.js"></script>

### Complex Parallel Builds

For large sites using a CI service it is possible to break up a build into parallel builds that each build for specific locales then combine the build results in a "fan-in" build after the locale specific builds.

<script src="https://gist.github.com/Zoramite/93f81a5a58afcb8cbbc474c891ff591c.js"></script>

## Using Travis CI for automatic deploys

1. Set up your deployment (both the host and the configuration in `podspec.yaml`).
1. Connect your GitHub repo with Travis CI.
1. Configure Travis CI.

To configure Travis CI, add a `.travis.yml` file in your repository's root. Any required access keys can be configured as secure environment variables in the _settings_ section of your Travis CI project.

```yaml
language: python
python:
- 2.7
branches:
  only:
  - master
cache: pip
install: pip install grow
script: grow deploy --noconfirm grow.io
```
