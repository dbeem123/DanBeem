"""Fail-closed SMS -> ComfyUI -> private Studio result orchestration.

No HTTP, Twilio, Discord, InvokeAI, or filesystem side effects are performed here.
Adapters and publisher are explicitly injected so this slice stays offline.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import re
from typing import Any, Protocol

PNG = b"\x89PNG\r\n\x1a\n"
LINK_BASE = "https://studio.danbeem.xyz/image/?id="

class ComfyAdapter(Protocol):
    provider: str
    def generate(self, prompt: str) -> bytes: ...

class ResultPublisher(Protocol):
    def publish_private(self, result_id: str, owner: str, data: bytes, mime: str) -> str: ...

@dataclass(frozen=True)
class InboundRequest:
    from_phone: str
    body: str
    message_sid: str
    signature: str
    raw_url: str = "https://sms.local/webhook"
    keyword_state: str = "normal"
    consent: bool = True
    a2p_approved: bool = True

@dataclass(frozen=True)
class Response:
    status: str
    detail: str
    message_sid: str
    body: str
    link: str | None = None

class DispatchError(ValueError): pass

class Dispatcher:
    """One-shot dispatcher with SID idempotency and strict owner/provider gates."""
    def __init__(self, *, owner_phone: str, signing_secret: bytes, adapter: ComfyAdapter,
                 publisher: ResultPublisher, owner_principal: str = "dan") -> None:
        self.owner_phone = owner_phone
        self.secret = signing_secret
        self.adapter = adapter
        self.publisher = publisher
        self.owner_principal = owner_principal
        self._seen: dict[str, Response] = {}
        if getattr(adapter, "provider", None) != "comfyui":
            raise DispatchError("comfyui_adapter_required")

    def sign(self, request: InboundRequest) -> str:
        message = request.raw_url + request.from_phone + request.body
        return hmac.new(self.secret, message.encode(), hashlib.sha256).hexdigest()

    def handle(self, request: InboundRequest) -> Response:
        sid = request.message_sid.strip()
        if not sid: return self._blocked("message_sid_required", sid)
        if sid in self._seen: return self._blocked("duplicate_message_sid", sid)
        if not hmac.compare_digest(request.signature, self.sign(request)):
            return self._remember(Response("blocked", "signed_webhook_required", sid, "Request rejected."))
        if request.from_phone != self.owner_phone:
            return self._remember(Response("blocked", "owner_authorization_required", sid, "Request rejected."))
        keyword = request.keyword_state.casefold().strip()
        if keyword == "stop": return self._remember(Response("blocked", "stop_blocks_outbound", sid, "Request rejected."))
        if keyword in {"start", "unstop", "help"}:
            return self._remember(Response("blocked", "provider_keyword_not_enrollment", sid, "Request rejected."))
        if not request.consent: return self._remember(Response("blocked", "danbot_opt_in_required", sid, "Request rejected."))
        if not request.a2p_approved: return self._remember(Response("blocked", "a2p_approval_required", sid, "Request rejected."))
        kind, prompt = self._classify(request.body)
        if kind != "image": return self._remember(Response("blocked", "image_intent_required", sid, "Image request required."))
        try:
            artifact = self.adapter.generate(prompt)
            self._validate_png(artifact)
            result_id = "sms-" + hashlib.sha256(sid.encode()).hexdigest()[:20]
            link = self.publisher.publish_private(result_id, self.owner_principal, artifact, "image/png")
            if link != LINK_BASE + result_id: raise DispatchError("publisher_link_mismatch")
        except (Exception,) as exc:
            return self._remember(Response("blocked", "dispatch_failed", sid, "Image request could not be completed."))
        return self._remember(Response("success", "private_result_published", sid, "Image ready: " + link, link))

    def _classify(self, body: str) -> tuple[str, str]:
        text = " ".join(body.strip().split())
        command, _, rest = text.partition(" ")
        if command.casefold() in {"image", "make-image", "imagine"} and rest.strip():
            prompt = rest.strip()
            if re.search(r"(?:^|\s)(?:to|recipient|send)\s+", prompt, re.I):
                return "unknown", ""
            return "image", prompt
        return "unknown", ""

    @staticmethod
    def _validate_png(data: bytes) -> None:
        if not isinstance(data, bytes) or len(data) < len(PNG) or not data.startswith(PNG):
            raise DispatchError("invalid_png_artifact")

    def _remember(self, response: Response) -> Response:
        self._seen[response.message_sid] = response
        return response

    def _blocked(self, detail: str, sid: str) -> Response:
        if sid in self._seen: return Response("blocked", "duplicate_message_sid", sid, "Request rejected.")
        return self._remember(Response("blocked", detail, sid, "Request rejected."))
