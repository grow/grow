---
$title: Deployment
$category: Workflow
$order: 2
---
# Deployment

[TOC]

Pods can be deployed in two ways: static and dynamic. For static deployment, a pod is built and the resulting fileset is deployed to the launch destination. For dynamic deployment, a pod is launched to a Grow PodServer, which then serves the pod up dynamically. Dynamic deployment is not yet available in the current version of Grow.

## Deployment types

### Static

Grow generates a static build of your website, and deploys that build to a static web server. Some web servers (such as S3 and GCS) can be autoconfigured by Grow and include features such as redirects, custom error pages, etc.

### Dynamic (not implemented)

Pods can be deployed to a dynamic PodServer for additional "dynamic" functionality. Dynamic functionality may include things such as forms, enforcing login, searching, etc.

## Launch process

### Steps

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

### Configuration

You can configure deployments by specifying them in `podspec.yaml`. The *deployments* key maps deployment names to destination configurations.

    # In podspec.yaml...

    deployments:

      default:                # Deployment name.
        destination: local    # Destination.
        out_dir: ~/out/       # Parameters for "local" destination.

      growsdk.org:
        destination: gcs
        bucket: preview.growsdk.org

### Commands

Once you've configured a deployment in `podspec.yaml`, you can use the `grow deploy` command to launch your site. This will kick off the deployment process (above).

    # Deploys your pod to the default destination.
    grow deploy <pod>

    # Deploys your site to a named destination.
    grow deploy growsdk.org <pod>

## Launch destinations

### Google Cloud Storage

There are two ways Grow can establish a connection to Google Cloud Storage. You can either use the "interoperable" method (which uses an access key and secret, similar to connections to Amazon S3), or you can use a client email address and key file.

    # Authenticates using access key and secret.
    deployments:
      name:
        destination: gcs
        bucket: mybucket.example.com

    # Authenticates using service account email and private key file.
    deployments:
      name:
        destination: gcs
        bucket: mybucket.example.com
        project: project-id
        email: 606734090113-6ink7iugcv89da9sru7lii8bs3i0obqg@developer.gserviceaccount.com
        key_path: /path/to/key/file.p12

To use the "interoperable" method, obtain an access key and secret from the Cloud Console, and place them in `$HOME/.boto`. [See documentation on obtaining access keys](https://developers.google.com/storage/docs/migrating#keys).

    # `$HOME/.boto`...

    [Credentials]
    gs_access_key_id = GOOGTS7C7FUP3AIRVJTE
    gs_secret_access_key = bGoa+V7g/yqDXvKRqq+JTFn4uQZbPiQJo4pf9RzJ

To use a client email and private key file, visit the Google Developers Console (`https://console.developers.google.com/project/apps~YOUR_PROJECT/apiui/credential`) and use the *email address* for the *Service Account* and download the key using the *Generate New Key* button. If you do not have a *Service Account* listed on this screen, use the *Create new Client ID* button.

In addition to obtaining your service account email address and key file, you must make sure that the service account has ownership access to the Google Cloud Storage bucket where you are deploying your site. To do this, make sure the service account's email address is in the bucket's ACL as a *User* and *Owner*. You can do this from the Developers Console Cloud Storage UI.

### Amazon S3

Deploys a build to an Amazon S3 bucket.

    deployments:
      name:
        destination: s3
        bucket: mybucket.example.com

To authenticate to Amazon S3, obtain your access key and secret and place them in `$HOME/.boto`.

    [Credentials]
    aws_access_key_id = ...
    aws_secret_access_key  = ...

### Local

Deploys a build to a local destination on your computer.

    deployments:
      name:
        destination: local
        out_dir: /path/to/out/directory/

### SCP

Authenticates using the ssh keys running in ssh-agent. The `root_dir` option uses syntax from the standard `scp` command. Values can be either absolute or relative. The `host` is required. `username` is optional and is used to specify the target server username if it differs from your development environment user issuing the `grow deploy` command.

    destinations:
      name:
        destination: scp
        host: example.com
        username: serverusername
        root_dir: /home/username/domains/example.com/public_html/

### Unimplemented builtin destinations

We would like to also add support for deployment to...

- Zip files
- Google App Engine
- Dropbox
- GitHub Pages
- Git

## Deployment index

<div class="badge badge-docs-incomplete">Documentation incomplete</div>

The deployment index is a record of deployment for each pod. The deployment index records the current state of the deployed site, which files exist, when they were deployed, and who performed the deployment. The deployment index is deployed along with generated files with each launch and used to display a diff before each deployment.
