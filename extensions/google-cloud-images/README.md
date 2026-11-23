# Google Cloud Images Extension (`grow-ext-google-cloud-images`)

An extension for hosting images in Google Cloud Storage and serving them via
Google's high-performance dynamic image-serving infrastructure.

> **Consolidated into the Grow monorepo.** The legacy standalone repository
> `grow/grow-ext-google-cloud-images` has been retired and archived; all
> development and security updates now live under
> `extensions/google-cloud-images/`.

## Features

- Generates URLs for images stored in Google Cloud Storage to serve them via
  Google's high-performance dynamic image-serving infrastructure.
- Appends image transformation options (size, crop, format, quality, rotation)
  to generated URLs.
- Supports localized images via `{locale}` filename placeholders.
- **Minimal dependencies**: the Grow extension uses only Python's standard
  library (zero extra third-party packages), and the App Engine backend uses a
  stdlib WSGI app requiring only `appengine-python-standard` and `gunicorn`.

## Security model

The backend microservice (`backend/main.py`) runs with an App Engine service
account that may have IAM permissions across multiple GCS buckets. To prevent
confused-deputy attacks, the backend enforces:

1. **Bucket allowlist (`ALLOWED_BUCKETS`)**: Set `ALLOWED_BUCKETS` to a
   comma-separated list of GCS bucket names. Any request targeting an unlisted
   bucket is rejected with `404` before any upstream call.
2. **Optional API key authentication (`API_KEY`)**: Set `API_KEY` to require
   `Authorization: Bearer <token>` or `X-API-Key: <token>` (compared in
   constant time). The Grow extension reads `GROW_GCI_API_KEY` from the
   environment automatically.
3. **Strict path & locale validation**: Rejects path traversal (`.`, `..`),
   query/fragment smuggling (`?`, `#`, `%`), backslashes, control characters,
   invalid GCS bucket names, and `{locale}` injection.
4. **Anonymous public-read verification first**: Queries the unauthenticated
   GCS JSON metadata endpoint with redirects disabled and verifies the returned
   `bucket` and `name` match the requested object *before* invoking App Engine
   Images APIs. Private or nonexistent objects return an identical empty `404`.
5. **Strictly read-only on `GET`**: No GCS object copies or metadata mutations
   are ever performed on `GET` requests, only allowlisted image/blob extensions
   are served, and `reset_cache` (`images.delete_serving_url`) is only permitted
   for authenticated callers (`403` otherwise).

## Setup

### 1. Deploy the App Engine backend

We recommend each project or organization deploy its own backend instance with
`ALLOWED_BUCKETS` (and optionally `API_KEY`) configured:

```shell
cd extensions/google-cloud-images/backend
make install
make project=GOOGLE_CLOUD_PROJECT_ID deploy
```

### 2. Configure Grow

Add to your pod's `extensions.txt`:

```text
git+https://github.com/grow/grow.git#subdirectory=extensions/google-cloud-images
```

Run `grow install`, then configure `podspec.yaml`:

```yaml
extensions:
  jinja2:
  - extensions.google_cloud_images.GoogleCloudImagesExtension
  preprocessors:
  - extensions.google_cloud_images.GoogleCloudImagesPreprocessor

preprocessors:
- kind: google_cloud_images
  backend: https://ext-cloud-images-dot-YOUR_PROJECT.appspot.com/
  rewrite_locales:
  - rewrite: en_AU
    to: en_GB
```

If your backend sets `API_KEY`, export `GROW_GCI_API_KEY=<token>` before
running `grow build` or `grow run`.

### 3. Google Cloud Storage bucket permissions

Ensure objects you want to serve are publicly readable (`allUsers: Storage Object Viewer`)
and that your App Engine service account has read access to the bucket:

```shell
gsutil mb -p <project> gs://<bucket>
gsutil iam ch allUsers:objectViewer gs://<bucket>
```

### 4. Usage in templates

```jinja
{# Default image URL #}
{{google_image("/bucket/folder/path.jpg").url()}}

{# Image URL with 1440 size option appended #}
{{google_image("/bucket/folder/path.jpg").url(['s1440'])}}

{# Localized image URL #}
{{google_image("/bucket/folder/path@{locale}.jpg").url()}}

{# Object properties #}
{% set image = google_image("/bucket/folder/path.jpg") %}
{{image.content_type}}
{{image.created}}
{{image.dimensions}}
{{image.etag}}
{{image.height}}
{{image.locale}}
{{image.size}}
{{image.url()}}
{{image.width}}
```
