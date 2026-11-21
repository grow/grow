---
$title: Deployment
$category: Workflow
$order: 10.3
---

Deployment is the act of taking your pod, generating a static site, and transferring it to a web server (or other location), typically ready for serving it publically to the world.

## Launch lifecycle

### Steps

The launch lifecycle remains the same regardless of your deployment's destination. Here are the steps that every launch undergoes:

1. __Processing__: All pre and post-processors used by your pod are run.
1. __Destination pre-launch__: A test is run to verify that Grow can connect to and configure your destination.
1. __Deployment index comparison__: The deployment index is retrieved from the destination (if it exists), and a diff between what's live and what's about to be deployed is presented to you for confirmation.
1. __Deployment__
    1. The diff between your local index and the deployment index is applied (new files are written, old files are deleted, and edits are made).
    1. The destination is configured (if applicable) with things like redirects, custom error pages, etc.
1. __Destination post-launch__: Any clean up tasks required by the destination are run.
    1. The deployment log is updated at the destination.
    1. The deployment index is written to the destination.

These universal steps ensure that every deployment remains consistent – and so that future deployments have knowledge of the previous deployment.

### Configuration

You can configure deployments by specifying them in `podspec.yaml`. The *deployments* key maps deployment names to destination configurations.

```yaml
# podspec.yaml

deployments:

  default:                # Deployment name.
    destination: local    # Destination kind.
    out_dir: ~/out/       # Parameters for "local" destination.

  grow.io:
    destination: gcs
    bucket: grow.io
```

### Commands

Once you've configured a deployment in `podspec.yaml`, you can use the `grow deploy` command to launch your site. This will kick off the deployment process (above).

```bash
# Deploys your site to a destination named `grow.io`.
grow deploy grow.io <pod>
```

## Destinations

### Google Cloud Storage

Deploys a build to Google Cloud Storage, appropriate for serving directly from GCS using the website serving feature.

There are two ways Grow can establish a connection to Google Cloud Storage. You can either use the "interoperable" method (which uses an access key and secret, similar to connections to Amazon S3), or you can use a client email address and key file.

```yaml
# Authenticates using access key and secret.
destination: gcs
bucket: mybucket.example.com

# Authenticates using service account email and private key file.
destination: gcs
bucket: mybucket.example.com
project: project-id
email: 606734090113-6ink7iugcv89da9sru7lii8bs3i0obqg@developer.gserviceaccount.com
key_path: /path/to/key/file.p12
```

To use the "interoperable" method, obtain an access key and secret from the Cloud Console, and place them in `$HOME/.boto`. You can alternatively place them in environment variables `GS_ACCESS_KEY_ID` and `GS_SECRET_ACCESS_KEY` instead of using the `.boto` file. [See documentation on obtaining access keys](https://developers.google.com/storage/docs/migrating#keys).

```ini
# `$HOME/.boto`
[Credentials]
gs_access_key_id = GOOGTS7C7FUP3AIRVJTE
gs_secret_access_key = bGoa+V7g/yqDXvKRqq+JTFn4uQZbPiQJo4pf9RzJ
```

To use a client email and private key file, visit the Google Developers Console (`https://console.developers.google.com/project/apps~YOUR_PROJECT/apiui/credential`) and use the *email address* for the *Service Account* and download the key using the *Generate New Key* button. If you do not have a *Service Account* listed on this screen, use the *Create new Client ID* button.

In addition to obtaining your service account email address and key file, you must make sure that the service account has ownership access to the Google Cloud Storage bucket where you are deploying your site. To do this, make sure the service account's email address is in the bucket's ACL as a *User* and *Owner*. You can do this from the Developers Console Cloud Storage UI.

### Amazon S3

Deploys a build to an Amazon S3 bucket, appropriate for serving directly from S3 using the website serving feature.

```yaml
destination: s3
bucket: mybucket.example.com
```

To authenticate to Amazon S3, obtain your access key and secret and place them in `$HOME/.boto`. You can also place these environment variables `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.

```ini
[Credentials]
aws_access_key_id = ...
aws_secret_access_key  = ...
```

### Local

Deploys a build to a local destination on your computer.

```yaml
destination: local
out_dir: /path/to/out/directory/
```

### SCP

Authenticates using the ssh keys running in ssh-agent. The `root_dir` option uses syntax from the standard `scp` command. Values can be either absolute or relative. The `host` is required. `port` is optional and will default to 22 if not specified. `username` is optional and is used to specify the target server username if it differs from your development environment user issuing the `grow deploy` command.

```yaml
destination: scp
host: example.com
port: 1111
username: username
root_dir: /home/username/domains/example.com/public_html/
```

### Git

Deploys a build to a Git repository (either remote or local). Remote repositories are first cloned to a temporary directory, then the specified branch is checked out. The deployment is applied, committed, and then (if the repository is remote), the branch is pushed to the origin. Unless specified otherwise by using the `path` field, builds are deployed to the root folder of the repository.

Git deployments can be used in conjunction with GitHub pages by specifying the `gh-pages` branch.

```yaml
destination: git
repo: https://github.com/owner/project.git
branch: master
root_dir: <optional base path within the repository>
```

## Deployment index

<div class="badge badge-docs-incomplete">Documentation incomplete</div>

The deployment index is a record of deployment for each pod. The deployment index records the current state of the deployed site, which files exist, when they were deployed, and who performed the deployment. The deployment index is deployed along with generated files with each launch and used to display a diff before each deployment.

## Environment

Deployments can specify environment parameters – for access in the `{{env}}` context variable. Use `{{env}}` to customize template behavior based on the deployment.

```yaml
env:
  name: prod
  host: example.com
  port: 80
  scheme: http
```
