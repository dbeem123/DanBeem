"""Cloudflare Access JWT validation with bounded JWKS resolution."""
from __future__ import annotations

import base64
import json
import os
import time
from threading import Lock
from typing import Any, Callable, Mapping
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import jwt
from jwt import InvalidTokenError


class AccessAuthError(ValueError):
    """Raised for any missing, malformed, expired, or untrusted Access token."""


class BoundedJWKSResolver:
    """Resolve and cache a small JWKS document; all resolver failures fail closed."""

    def __init__(self, url: str, *, timeout: float = 3.0, max_bytes: int = 256 * 1024,
                 max_keys: int = 32, ttl: float = 300.0, opener=urlopen):
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("JWKS_URL must be an HTTPS URL")
        if timeout <= 0 or max_bytes <= 0 or max_keys <= 0 or ttl <= 0:
            raise ValueError("JWKS resolver bounds must be positive")
        self.url, self.timeout, self.max_bytes = url, timeout, max_bytes
        self.max_keys, self.ttl, self._opener = max_keys, ttl, opener
        self._lock = Lock()
        self._cached: tuple[float, Mapping[str, Any]] | None = None

    def __call__(self, kid: str) -> Mapping[str, Any]:
        now = time.monotonic()
        with self._lock:
            if self._cached and now < self._cached[0]:
                return self._cached[1]
            try:
                request = Request(self.url, headers={"Accept": "application/json"}, method="GET")
                with self._opener(request, timeout=self.timeout) as response:
                    raw = response.read(self.max_bytes + 1)
                if len(raw) > self.max_bytes:
                    raise ValueError("JWKS response too large")
                document = json.loads(raw.decode("utf-8"))
                keys = document.get("keys") if isinstance(document, Mapping) else None
                if not isinstance(keys, list) or len(keys) > self.max_keys:
                    raise ValueError("invalid or oversized JWKS")
                # Cache only structurally valid JSON; key selection and cryptographic
                # validation remain the validator's responsibility.
                self._cached = (now + self.ttl, document)
                return document
            except Exception as exc:
                # Do not retain stale keys after a resolver error: fail closed.
                self._cached = None
                raise AccessAuthError("JWKS unavailable") from exc


class AccessJWTValidator:
    """Validate Access JWTs with strict issuer, audience, algorithm, key and time checks."""

    def __init__(self, issuer: str, audience: str, resolve_jwks: Callable[[str], Mapping[str, Any]], *,
                 algorithms: tuple[str, ...] = ("RS256",), clock: Callable[[], float] = time.time,
                 max_jwks_bytes: int = 256 * 1024, max_keys: int = 32):
        if not issuer or not audience or not callable(resolve_jwks):
            raise ValueError("issuer, audience, and JWKS resolver are required")
        if not algorithms or any(a.lower() == "none" or not a for a in algorithms):
            raise ValueError("a non-empty safe algorithm allowlist is required")
        self.issuer, self.audience = issuer.rstrip("/"), audience
        self.resolve_jwks, self.algorithms, self.clock = resolve_jwks, algorithms, clock
        self.max_jwks_bytes, self.max_keys = max_jwks_bytes, max_keys

    @classmethod
    def from_env(cls, *, clock=time.time) -> "AccessJWTValidator":
        issuer = os.environ.get("DANBOT_ACCESS_ISSUER", "")
        audience = os.environ.get("DANBOT_ACCESS_AUDIENCE", "")
        jwks_url = os.environ.get("DANBOT_ACCESS_JWKS_URL", "")
        if not issuer or not audience or not jwks_url:
            raise ValueError("DANBOT_ACCESS_ISSUER, DANBOT_ACCESS_AUDIENCE, and DANBOT_ACCESS_JWKS_URL are required")
        return cls(issuer, audience, BoundedJWKSResolver(jwks_url), clock=clock)

    def principal(self, token: str | None) -> str:
        if not token:
            raise AccessAuthError("missing Access token")
        try:
            header = jwt.get_unverified_header(token)
            alg, kid = header.get("alg"), header.get("kid")
            if alg not in self.algorithms or not isinstance(kid, str) or not kid or len(kid) > 256:
                raise AccessAuthError("unsupported token header")
            jwks = self.resolve_jwks(kid)
            encoded = json.dumps(jwks, separators=(",", ":"), sort_keys=True).encode()
            if len(encoded) > self.max_jwks_bytes:
                raise AccessAuthError("JWKS response too large")
            keys = jwks.get("keys") if isinstance(jwks, Mapping) else None
            if not isinstance(keys, list) or len(keys) > self.max_keys:
                raise AccessAuthError("invalid JWKS response")
            jwk = next((k for k in keys if isinstance(k, Mapping) and k.get("kid") == kid and k.get("alg", alg) == alg), None)
            if not jwk:
                raise AccessAuthError("unknown key id")
            key = jwt.algorithms.get_default_algorithms()[alg].from_jwk(json.dumps(jwk))
            claims = jwt.decode(token, key, algorithms=[alg], options={"require": ["exp", "iss", "aud"], "verify_exp": False, "verify_nbf": False, "verify_iss": False, "verify_aud": False})
            if str(claims.get("iss", "")).rstrip("/") != self.issuer:
                raise AccessAuthError("issuer mismatch")
            aud = claims.get("aud")
            if not (aud == self.audience or isinstance(aud, list) and self.audience in aud):
                raise AccessAuthError("audience mismatch")
            now = self.clock(); exp = claims.get("exp"); nbf = claims.get("nbf", now)
            if isinstance(exp, bool) or not isinstance(exp, (int, float)) or now >= exp:
                raise AccessAuthError("expired token")
            if isinstance(nbf, bool) or not isinstance(nbf, (int, float)) or now < nbf:
                raise AccessAuthError("token not active")
            principal = claims.get("email") or claims.get("sub")
            if not isinstance(principal, str) or not principal.strip():
                raise AccessAuthError("token has no principal")
            return principal.strip()
        except AccessAuthError:
            raise
        except (InvalidTokenError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise AccessAuthError("invalid Access token") from exc
