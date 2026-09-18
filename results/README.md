# DanBot image and song result pages

This change adds static, responsive result viewers at `/image/?id=<result_id>` and `/song/?id=<result_id>`. The pages do **not** generate media, host files, authenticate users, or enable SMS sending. They are front-end shells intended for Hermes / BeemOps to connect later. Do not announce image or song delivery as operational until the end-to-end integration has passed testing. Existing `/sms/`, privacy, and terms language must remain accurate.

## Required backend (NOT implemented in this repository)

Serve a protected API at the **same origin** as these pages: `GET /api/results/{result_id}`. The static GitHub Pages hosting for `danbeem.xyz` cannot handle this route; a trusted same-origin reverse proxy, gateway, or an alternative authenticated hosting deployment is needed before functionality can be enabled. Do not point the public page at the private Hermes gateway or publish its credentials. Fail closed until the API and hosting are ready. Implement signed-in sessions (secure, HttpOnly, SameSite cookies), per-result authorization, server-side rate limiting, expiration/retention, media MIME and size validation, CSP, anti-indexing response headers, and no-store response caching. Prevent ID enumeration and unauthorized cross-user access. Ensure the actual media and download endpoints also enforce authorization; never rely on an unguessable ID or the client's same-origin URL check alone.

Authenticated JSON response example (illustrative only):

```json
{
  "id": "Abcd1234_Example5678",
  "type": "image",
  "status": "complete",
  "title": "Beach postcard",
  "description": "Generated for your request",
  "created_at": "2026-09-18T12:00:00Z",
  "media": {
    "mime_type": "image/png",
    "url": "/api/results/Abcd1234_Example5678/media",
    "download_url": "/api/results/Abcd1234_Example5678/download"
  },
  "sharing": { "enabled": false }
}
```

Set `type` to `song` and use an allowed audio MIME such as `audio/mpeg` for music. Set `status` to `queued`, `processing`, `failed`, or `complete`. Incomplete states do not need `media`. Return 401 for unauthenticated, 403 for unauthorized, and 404/410 for unavailable or expired results. Do not leak result details to unauthorized clients. Do not expose provider API keys, private prompts, phone numbers, or internal filesystem paths in responses. Never publish real user media to this public git repository.

## Hermes / Twilio integration

1. Authorize and record the originating user's request in the trusted backend. SMS consent is separate from permission to use private tools or access another person's result.
2. Generate the image or song through a provider actually installed, configured, licensed, and authorized for the request. Maintain explicit status and secure media storage. This PR does not select or integrate a generation provider.
3. Associate each result with its owner. Expose metadata and file bytes only through authenticated, owner-scoped routes. Any sharing feature requires an explicit grant with restricted audience and expiry, plus a revocation path. Leave `sharing.enabled` false until implemented.
4. Only after real end-to-end testing, send the appropriate `/image/?id=...` or `/song/?id=...` link by an approved SMS channel. Do not include API credentials or publicly accessible media URLs in texts. Twilio's A2P registration is separately pending as of the latest email check and is not made approved by deploying these pages.
5. Test desktop/mobile screen readers, audio controls, image alternative text, expired/invalid IDs, no API, 401/403/404, provider failures, rejected MIME and origin, concurrent users, and download permissions before rollout.

## Deployment note

This change is on a feature branch for review. Even if the static pages are later merged to `main`, without a same-origin protected backend they will display a clear *Result service unavailable* message, rather than fake media or publicly expose content. Avoid adding links to the main homepage that suggest an operational service until the backend is connected.
