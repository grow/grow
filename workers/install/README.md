# Legacy Install URL Worker (`install.grow.io` / `install.growsdk.org`)

Cloudflare Worker (`grow-install-deprecated`) that serves the retirement notice for the legacy `curl https://install.grow.io | bash` and `curl https://install.growsdk.org | bash` one-liners without requiring `-L` or any GCP infrastructure.

## How it works

1. DNS for `install.grow.io` and `install.growsdk.org` uses proxied placeholder `AAAA 100::` records in Cloudflare.
2. Cloudflare routes `install.grow.io/*` and `install.growsdk.org/*` to this Worker.
3. The Worker fetches and caches `https://grow.dev/install.sh` (built from `docs/source/root/install.sh` on GitHub Pages) and returns `HTTP 200` (`text/plain; charset=utf-8`), falling back to the inline deprecation script if GitHub Pages is unavailable.

## Updating

- To update the message text, edit `docs/source/root/install.sh` (and keep `FALLBACK_SCRIPT` in `worker.js` in sync).
- To redeploy the Worker:
  ```bash
  npx wrangler deploy
  ```
