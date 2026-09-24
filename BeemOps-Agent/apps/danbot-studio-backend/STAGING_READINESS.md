# DB-3080 local staging operations

## Artifacts

- `launch_backend.cmd` resolves the repository `.venv\Scripts\python.exe` without relying on the caller's current directory, binds the backend to `127.0.0.1:8765`, and uses this directory's `danbot_studio.sqlite3` and `artifacts` paths.
- `DanBotStudioBackend-LocalStaging.xml` is an import-ready, disabled, least-privilege task definition. It is intentionally **not registered or run** by this slice.
- `.env.example` documents only the non-secret Cloudflare Access issuer, audience, and JWKS URL names. The current CLI does not construct an Access validator and does not need credentials. Never place credentials in this directory or task XML.

## Readiness checklist

1. Create/update the dedicated environment offline:
   `.venv\Scripts\python.exe -m pip install -r requirements.txt`
2. Verify syntax and offline behavior:
   `.venv\Scripts\python.exe -m py_compile backend.py access_auth.py test_backend.py test_staging_startup.py`
   `.venv\Scripts\python.exe -m unittest -v test_backend.py test_staging_startup.py`
3. Start manually for local staging only: `launch_backend.cmd`.
4. Confirm only loopback is used: browse `http://127.0.0.1:8765` (the root intentionally returns 404) and check the process is the dedicated `.venv` Python.
5. Review the task XML before any separate approval to import. This artifact does not prove task registration, execution, Cloudflare routing, DNS, or public availability.

The Access issuer/audience/JWKS values are deployment configuration inputs for a future reviewed integration. This offline slice performs no network JWKS discovery and logs no environment values.

## Rollback

- Stop the manually started process with `Ctrl+C`.
- Do not unregister anything for this slice: no task was registered.
- To discard this staging slice, remove this directory, or stop the process and remove only `danbot_studio.sqlite3*` and `artifacts\`. No production paths are referenced.
- Do not delete or alter Cloudflare, DNS, tunnel, Twilio, protected bot/Hermes, Kanban, public-site, or media assets as rollback actions.

## Scope / limits

This is local staging preparation only. It does not save a Cloudflare route, change DNS, modify tunnel routes, expose media, or configure real authentication credentials.
