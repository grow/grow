---
$title: Continuous integration
$category: Workflow
$order: 3
---
# Continuous integration

[TOC]

You can easily test, build, and/or deploy your website using a continuous integration (CI) system. CI systems remove extra steps from your project's lifecycle and allow you to save time on repetitive tasks.

## Using Travis CI for automatic deploys

The combination of GitHub, Travis CI, Grow SDK, and a static hosting service such as Google Cloud Storage or Amazon S3 allow you and your team to collaborate on Git and keep your site automatically up to date – without ever having to run a deploy command.

In fact, this is [exactly how this documentation is deployed](https://github.com/grow/growsdk.org).

1. Set up your deployment (both the host and the configuration in `podspec.yaml`).
1. Connect your GitHub repo with Travis CI.
1. Configure Travis CI.

To configure Travis CI, add a `.travis.yml` file in your repository's root.

[sourcecode:yaml]
language: python
python:
- 2.7
branches:
  only:
  - master
install:
- git clone https://github.com/grow/pygrow.git
- cd pygrow
- travis_retry pip install -r requirements.txt
- python setup.py install
- cd ..
script: ./pygrow/bin/grow deploy --noconfirm growsdk.org
[/sourcecode]
