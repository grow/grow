# Editor Extension (`grow-ext-editor`)

Inline content editor extension for Grow's local development server.

- Updated for Python 3.10+ and Jinja2 3.x / Werkzeug 3.x (removed legacy
  `werkzeug==1.0.1` pin and removed deprecated Jinja2 extensions).
- Hardened pod API endpoints against path traversal (`..`, absolute/escaped
  filenames, and unsafe upload destinations).

## Installation

Add to `extensions.txt`:

```text
git+https://github.com/grow/grow.git#subdirectory=extensions/editor
```
