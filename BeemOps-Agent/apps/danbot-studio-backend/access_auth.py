"""Offline-verifiable Cloudflare Access JWT validation."""
from __future__ import annotations

import json
import os
import time
from typing import Any, Callable, Mapping

import jwt
from jwt import InvalidTokenError


class AccessAuthError(ValueError):
    """Raised for any missing, malformed, expired, or untrusted Access token."""


class AccessJWTValidator:
    """Validate Cloudflare Access JWTs against a bounded, injected JWKS resolver.

    The resolver is deliberately injected: this class never performs network I/O.
    It may return a JWKS mapping or a single JWK mapping. The resolver should be a
    reviewed cache in production and must return only keys for the configured team.
    """

    def __init__(
        self,
        issuer: str,
        audience: str,
        resolve_jwks: Callable[[str], Mapping[str, Any]],
        *,
        algorithms: tuple[str, ...] = ("RS256",),
        clock: Callable[[], float] = time.time,
        max_jwks_bytes: int = 256 * 1024,
    ):
        if not issuer or not audience or not callable(resolve_jwks):
            raise ValueError("issuer, audience, and JWKS resolver are required")
        if not algorithms or any(a in {"none", ""} for a in algorithms):
            raise ValueError("a non-empty safe algorithm allowlist is required")
        if max_jwks_bytes <= 0:
            raise ValueError("max_jwks_bytes must be positive")
        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.resolve_jwks = resolve_jwks
        self.algorithms = algorithms
        self.clock = clock
        self.max_jwks_bytes = max_jwks_bytes

    @classmethod
    def from_env(cls, resolver: Callable[[str], Mapping[str, Any]], *, clock=time.time):
        """Build from exact staging names; JWKS itself remains resolver-owned."""
        issuer = os.environ.get("DANBOT_ACCESS_ISSUER", "")
        audience = os.environ.get("DANBOT_ACCESS_AUDIENCE", "")
        if not issuer or not audience:
            raise ValueError("DANBOT_ACCESS_ISSUER and DANBOT_ACCESS_AUDIENCE are required")
        return cls(issuer, audience, resolver, clock=clock)

    def principal(self, token: str | None) -> str:
        if not token:
            raise AccessAuthError("missing Access token")
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") not in self.algorithms or not header.get("kid"):
                raise AccessAuthError("unsupported token header")
            jwks = self.resolve_jwks(str(header["kid"]))
            if not isinstance(jwks, Mapping):
                raise AccessAuthError("invalid JWKS response")
            encoded = json.dumps(jwks, separators=(",", ":"), sort_keys=True).encode()
            if len(encoded) > self.max_jwks_bytes:
                raise AccessAuthError("JWKS response too large")
            keys = jwks.get("keys")
            if keys is not None:
                if not isinstance(keys, list) or len(keys) > 32:
                    raise AccessAuthError("JWKS key set is too large")
                jwk = next((k for k in keys if isinstance(k, Mapping) and k.get("kid") == header["kid"]), None)
            else:
                jwk = jwks if jwks.get("kid") == header["kid"] else None
            if not jwk:
                raise AccessAuthError("unknown key id")
            key = jwt.algorithms.get_default_algorithms()[header["alg"]].from_jwk(json.dumps(jwk))
            claims = jwt.decode(
                token,
                key,
                algorithms=list(self.algorithms),
                issuer=self.issuer,
                audience=self.audience,
                leeway=0,
                options={"require": ["exp", "iss", "aud"], "verify_exp": False, "verify_nbf": False, "verify_iss": False, "verify_aud": False},
            )
            if str(claims.get("iss", "")).rstrip("/") != self.issuer:
                raise AccessAuthError("issuer mismatch")
            aud = claims.get("aud")
            if not (aud == self.audience or isinstance(aud, list) and self.audience in aud):
                raise AccessAuthError("audience mismatch")
            now = self.clock()
            if not isinstance(claims.get("exp"), (int, float)) or now >= claims["exp"]:
                raise AccessAuthError("expired token")
            if "nbf" in claims and (not isinstance(claims["nbf"], (int, float)) or now < claims["nbf"]):
                raise AccessAuthError("token not active")
        except (AccessAuthError, InvalidTokenError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            if isinstance(exc, AccessAuthError):
                raise
            raise AccessAuthError("invalid Access token") from exc
        principal = claims.get("email") or claims.get("sub")
        if not isinstance(principal, str) or not principal.strip():
            raise AccessAuthError("token has no principal")
        return principal.strip()
