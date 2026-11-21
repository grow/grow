---
$title: Deployment
$category: Workflow
$order: 10.3
---
# Deployment

Grow compiles your pod into a directory of static files that can be hosted anywhere — GitHub Pages, Cloudflare Pages, Netlify, Google Cloud Storage, Amazon S3, or any standard web server.

## Deploying with `grow build` (Recommended)

For most projects, the simplest deployment workflow is to run `grow build` in CI (for example, GitHub Actions) and publish the resulting `build/` directory to your static host.

See [Continuous integration]([url('/content/docs/workflow/continuous.md')]) for a complete GitHub Actions + GitHub Pages workflow.

## Built-in `grow deploy` destinations

If you want Grow to manage incremental diffs and upload files directly, define named destinations under `deployments:` in `podspec.yaml` and run `grow deploy <name>`:

```yaml
# podspec.yaml
deployments:
  local:
    destination: local
    out_dir: ./dist/

  pages:
    destination: git
    repo: https://github.com/owner/project.git
    branch: gh-pages
```

```bash
grow deploy pages
```

### Launch lifecycle

Every `grow deploy` follows the same predictable lifecycle:

1. **Preprocess & build**: Configured preprocessors run and all routes are rendered.
2. **Diff against deployment index**: Grow compares the newly built files against the destination's deployment index and shows a diff of additions, edits, and deletions for confirmation (pass `--noconfirm` in CI).
3. **Apply changes**: Only modified files are written and removed routes are deleted cleanly, then the deployment index is updated.

### Local destination

Writes the built site (with diff tracking) to a local directory on disk:

```yaml
destination: local
out_dir: /path/to/output/
```

### Git destination

Clones a Git repository, checks out the target branch, applies the build diff, commits, and pushes. Useful for branch-based hosting such as `gh-pages`:

```yaml
destination: git
repo: https://github.com/owner/project.git
branch: gh-pages
root_dir: ""  # Optional subdirectory within the repository.
```

## Deployment environments

Each deployment can define an `env` block exposed to templates as `{{env}}`, allowing you to adjust canonical URLs, analytics, or robots behavior per target:

```yaml
deployments:
  prod:
    destination: local
    out_dir: ./build/
    env:
      name: prod
      host: example.com
      port: 443
      scheme: https
```
