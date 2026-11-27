const FALLBACK_SCRIPT = `#!/usr/bin/env bash
set -euo pipefail

cat >&2 <<'EOF'

========================================================================
Notice: The standalone Grow binary installer (install.grow.io / install.py)
has been deprecated and retired.
========================================================================

Grow no longer publishes standalone binary zips on GitHub Releases.
Please migrate to installing Grow from PyPI (requires Python 3.10 - 3.12)
or using the official Docker image:

  1. Install globally with uv (recommended):
       uv tool install grow

  2. Or install with pip:
       pip install grow

  3. Or run via Docker (no local Python setup required):
       docker run --rm -it -v "$PWD":/site -w /site grow/base grow build

Full installation guide: https://grow.dev/install/

EOF

exit 1
`;

export default {
  async fetch(request) {
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      return new Response('Method Not Allowed\n', {status: 405});
    }
    try {
      const upstream = await fetch('https://grow.dev/install.sh', {
        cf: {cacheTtl: 3600, cacheEverything: true},
      });
      if (upstream.ok) {
        const body = request.method === 'HEAD' ? null : await upstream.text();
        return new Response(body, {
          status: 200,
          headers: {
            'content-type': 'text/plain; charset=utf-8',
            'cache-control': 'public, max-age=3600',
            'x-content-type-options': 'nosniff',
          },
        });
      }
    } catch (_) {}
    return new Response(request.method === 'HEAD' ? null : FALLBACK_SCRIPT, {
      status: 200,
      headers: {
        'content-type': 'text/plain; charset=utf-8',
        'cache-control': 'public, max-age=3600',
        'x-content-type-options': 'nosniff',
      },
    });
  },
};
