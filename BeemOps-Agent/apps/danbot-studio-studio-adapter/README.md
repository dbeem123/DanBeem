# DanBot Studio adapter — local staging

This isolated, loopback-only adapter serves the image and song viewer shells at
`/image/` and `/song/`, and proxies only same-origin `/v1/*` requests to the
existing backend at fixed `127.0.0.1:8765`. It forwards Cloudflare Access
headers, cookies, and Origin without embedding credentials. Responses are
`private, no-store` and `X-Robots-Tag: noindex`; all other paths return 404.

## Launch / readiness

From this directory:

```text
python adapter.py --host 127.0.0.1 --port 8787
```

With the backend separately running on loopback port 8765, verify:

```text
python -m unittest -v test_adapter.py
python -m py_compile adapter.py test_adapter.py
```

Then browse only `http://127.0.0.1:8787/image/` or `/song/`. No Cloudflare,
DNS, tunnel, public hosting, Twilio, protected bot/Hermes, Kanban, or live
media changes are part of this slice.

## Rollback

Stop the adapter with `Ctrl+C`; no service/task registration is performed.
Delete this directory to remove the slice. Do not change upstream backend,
Cloudflare, DNS, tunnel routes, or any media as rollback actions.
