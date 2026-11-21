---
$title: Continuous integration
$category: Workflow
$order: 10.4
---

You can easily test, build, and deploy your website using a continuous integration (CI) system. CI systems automate repetitive build steps and keep your published site in sync with Git.

The combination of GitHub, GitHub Actions, Grow, and a static host such as GitHub Pages, Google Cloud Storage, or Amazon S3 lets your team collaborate on Git and deploy automatically on every merge.

In fact, this is [exactly how this documentation is deployed](https://github.com/grow/grow/blob/main/.github/workflows/docs.yml).

For security, store deployment credentials as encrypted repository secrets in your CI provider rather than committing them to your repository.

## Using GitHub Actions and GitHub Pages

Create `.github/workflows/deploy.yml` in your repository to build your Grow pod with `uv` and publish the output to GitHub Pages on every push to `main`:

```yaml
name: Deploy site

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.10"
      - name: Build site
        run: uvx grow build .
      - uses: actions/upload-pages-artifact@v3
        with:
          path: build

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

## Deploying to Cloud Storage or S3

To deploy to a destination configured in `podspec.yaml` (such as Google Cloud Storage or Amazon S3), configure the required provider credentials as GitHub Actions secrets and run:

```yaml
- name: Deploy site
  run: uvx grow deploy --noconfirm prod
```

## Docker image

Grow also publishes a prebuilt Docker image on [Docker Hub (`grow/base`)](https://hub.docker.com/r/grow/base/) and GitHub Container Registry (`ghcr.io/grow/grow`) with Grow, Python, Node.js, and `gcloud` preinstalled.
