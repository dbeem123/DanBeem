# Luna Low local Studio same-origin integration proof — 2026-09-24

## Scope

Only `apps/danbot-studio-studio-adapter` was changed, plus this new proof file. No Cloudflare/DNS/tunnel, public site, Twilio, protected bot/Hermes, Kanban, or live media changes were made.

## Delivered

- Replaced image/song shells with full private viewers using shared `result.js` and `result.css`.
- Viewers use same-origin `/v1/results/{id}/{metadata,media,download}` only.
- Safe result IDs are validated in browser and adapter; adapter denies unknown result routes.
- Protected media/download URLs must be same-origin `/v1/results/…`; fetch uses same-origin credentials and `no-store`.
- Private/no-store/noindex headers remain on viewer and proxied API responses.
- 401/403/404/410 errors are surfaced truthfully by the viewer.
- Adapter forwards JWT/cookie/origin headers but explicitly does not forward Cloudflare service-token client ID/secret headers.
- Added synthetic local Node smoke harness covering viewer asset, API proxy, same-origin contract, and invalid ID path.

## Verification

- `python -m unittest -v test_adapter.py` — **6 passed**.
- `python -m py_compile adapter.py test_adapter.py` — **passed**.
- `node --check smoke_viewer_api.js` — **passed**.
- `node smoke_viewer_api.js` — **passed**.

## External gate

Cloudflare/DNS/tunnel configuration remains intentionally untouched and is the next external configuration gate.
