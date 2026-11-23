# Greenhouse Extension (`grow-ext-greenhouse`)

Grow preprocessor for importing job postings and education metadata from the
Greenhouse Job Board API, plus an optional App Engine submission proxy backend.

- **Zero extra 3P dependencies** in the Grow extension (uses Python stdlib
  `urllib.request` and an `html.parser` allowlist sanitizer instead of
  `requests` and archived `bleach`).
- **Hardened backend** (`backend/main.py`): stdlib Python 3.12 WSGI app
  (`gunicorn` only) enforcing `ALLOWED_BOARD_TOKENS`, strict `board_token` and
  `job_id` validation, and explicit `CORS_ALLOWED_ORIGINS` to prevent
  confused-deputy abuse of `GREENHOUSE_API_KEY`.

## Installation

Add to `extensions.txt`:

```text
git+https://github.com/grow/grow.git#subdirectory=extensions/greenhouse
```
