# DanBot Studio SMS dispatcher (Luna Low)

Offline-only proof slice. `dispatcher.py` is framework-neutral and performs no network,
Twilio, Discord, Cloudflare, Hermes, InvokeAI, or live SMS work.

## Contract

`Dispatcher.handle(InboundRequest)` fails closed on unsigned requests, non-owner
numbers, STOP/provider keyword states, missing consent, missing A2P approval, duplicate
Message SIDs, non-image intent, arbitrary recipient syntax, non-ComfyUI providers, and
invalid PNG artifacts. A successful injected `ComfyAdapter` result is validated by PNG
magic bytes, sent to an injected private `ResultPublisher`, and returns exactly one
truthful `https://studio.danbeem.xyz/image/?id=...` link. The publisher is responsible
for composing the protected Studio backend's private result contract; this slice never
calls that backend.

The `comfyui` provider check is intentionally explicit; `invokeai` is rejected.

## Verification

From this directory:

```text
python -m unittest -v
python -m compileall -q .
```

## Exact later runtime integration gate

Do **not** wire this into a runtime until all of the following are reviewed and passed:

1. Obtain explicit approval to modify the SMS ingress/runtime boundary; this proof
   slice alone grants no production authorization.
2. Adapt the real Twilio webhook verifier to construct `InboundRequest` with the exact
   signed URL, raw body, Message SID, sender, keyword state, durable opt-in, and A2P
   approval state. Never trust client-supplied booleans.
3. Provide a production ComfyUI adapter implementing the T03 API prompt/history/view
   contract, restricted to the approved local ComfyUI endpoint and workflow; reject
   every other provider name.
4. Provide a protected Studio backend publisher that authenticates as the owner,
   validates PNG bytes, stores privately, and returns the canonical result id. Verify
   the returned id is bound to the same owner and artifact.
5. Add durable, transactional SID idempotency and replay tests at the ingress boundary.
6. Run the full security/A2P review, staging-only end-to-end test, and independent
   production readiness review. Only then may a separately approved deployment change
   invoke this dispatcher. No SMS or Discord send is authorized by this repository
   slice.
