# DanBot Studio protected backend — DB-3080 local staging

Isolated localhost-only staging slice composing the T05/T06 result-service shape. Standard-library Python, durable SQLite metadata/audit/invitation records, and private artifact files. Synthetic fixtures only. Nothing here changes the public site, Cloudflare/DNS, Twilio, protected bot.py, Hermes, Kanban, or live media.

## Verified auth contract

- The future edge is Cloudflare Access; the backend accepts only `CF-Access-JWT-Assertion` and fails closed when it is missing or invalid.
- `access_auth.py` validates issuer, audience, `exp`, optional `nbf`, an allowlisted algorithm, `kid`, and a non-empty `email`/`sub` principal using PyJWT + cryptography. JWKS resolution is injected and bounded (max 32 keys / 256 KiB); this code never performs network I/O.
- Owner/invitation authorization remains backend-enforced after Access identity extraction: owner-only publish conflict handling, invitation, and revoke; invited principal may redeem and access media.
- Private metadata/media/download routes; 401 unauthenticated, 403 unauthorized, 404 missing/non-listing, 410 expired/revoked/integrity-invalid.
- Binds only to `127.0.0.1`; no LAN/public listener. Synthetic fixtures only.

## Cloudflare Access application fields (future operator configuration)

Configure these in a separately reviewed Cloudflare Access application; do not put values or secrets in this repository:

- **Application type:** Self-hosted
- **Application domain/path:** the future backend hostname and exact `/v1/*` path scope
- **Identity providers:** explicitly approved providers only
- **Session duration:** approved policy value; keep compatible with backend JWT `exp`
- **Audience (`aud`):** the Access application AUD tag; inject the same value into the backend validator configuration
- **Issuer (`iss`):** the Access team issuer URL, normalized without a trailing slash
- **JWT header:** Cloudflare Access must send `CF-Access-JWT-Assertion` to the origin
- **JWKS:** Access team JWKS endpoint, consumed only by a reviewed cache/resolver; never hardcode private keys
- **Policy:** allow only approved owner/invite identities; default deny

## Exact future route gate

For every future `/v1/*` route, before parsing the request body or accessing result data, run:

```text
principal = access_validator.principal(request.headers.get("CF-Access-JWT-Assertion"))
if not principal: return 401
then apply Store.status(row, principal) and the owner/invitation checks
```

The current `Handler` implements this gate through `Store.auth`; no route may bypass it. A real deployment must wire a maintained JWT/JWK library into `AccessJWTValidator`, configure issuer/audience out-of-band, and supply a bounded JWKS cache. This staging prototype intentionally does not perform network discovery.

## Existing backend protections

- SQLite durability for results, access, invitations, and audit events; filesystem artifacts are private and path-contained.
- MIME magic-byte, maximum-size, SHA-256, stored-size, safe-result-id, and path checks.
- Same owner/result/hash publish is idempotent; conflicting publish is 409.
- Every response includes `private, no-store`, `noindex`, and `no-cache` headers.

## Exact backend configuration names

Set these values only in the deployment environment or secret/configuration manager; never commit real values:

```text
DANBOT_ACCESS_ISSUER=https://<team-name>.cloudflareaccess.com
DANBOT_ACCESS_AUDIENCE=<Access application AUD tag>
DANBOT_ACCESS_JWKS_URL=https://<team-name>.cloudflareaccess.com/cdn-cgi/access/certs
```

`AccessJWTValidator.from_env(resolver)` reads the first two names. A separately reviewed resolver/cache may use `DANBOT_ACCESS_JWKS_URL` outside this module; tests must use a deterministic fake resolver and must not fetch it. Keep the resolver bounded and refresh keys only through an approved deployment mechanism.

## Offline tests and dependency installation

```text
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m unittest -v test_backend.py
.venv/Scripts/python.exe -m py_compile backend.py access_auth.py test_backend.py
```

Tests use a deterministic fake JWKS resolver and generated in-memory RSA keys. They make no network calls.

## Launch exact local staging

```text
python backend.py --port 8765 --db danbot_studio.sqlite3 --artifacts artifacts
```

The CLI is intentionally not production-wired with an Access validator; use the test/integration constructor (`serve(..., access_validator=...)`) for offline staging. Do not expose the port, add a reverse proxy, or use real media/secrets.

The reviewed staging dependency is pinned in `requirements.txt`: PyJWT 2.14.0 with cryptography 50.0.1. The validator is production-shaped but intentionally requires deployment wiring for the bounded JWKS cache/resolver and the real Cloudflare issuer/audience values. No network discovery is implemented here.
## Rollback / cleanup

Stop with `Ctrl+C`. To roll back this staging slice, stop the process and delete this directory (or remove only the supplied `--db` and `--artifacts` paths). No production files are referenced.
