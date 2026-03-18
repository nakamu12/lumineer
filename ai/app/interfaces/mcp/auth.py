"""OAuth 2.1 JWT validation for the MCP server.

Implements the Resource Server role in the OAuth 2.1 flow:
  - Validates Bearer tokens issued by Keycloak (or any OIDC-compliant AS)
  - Exposes Protected Resource Metadata (RFC 9728) at
    /.well-known/oauth-protected-resource

Auth is **optional** in dev (KEYCLOAK_URL not set) and **enforced** in prod
when MCP_REQUIRE_AUTH=true.  FastMCP automatically exposes the
/.well-known/oauth-protected-resource/mcp metadata endpoint when
AuthSettings are configured — no custom middleware is needed.
"""

from __future__ import annotations

import logging
from typing import Any

import jwt
from jwt import PyJWKClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JWT validation
# ---------------------------------------------------------------------------


class JWTValidator:
    """Validates JWT tokens against a JWKS endpoint (e.g., Keycloak)."""

    def __init__(
        self,
        jwks_uri: str,
        issuer: str,
        audience: str | None = None,
        algorithms: list[str] | None = None,
    ) -> None:
        self._jwks_client = PyJWKClient(jwks_uri, cache_keys=True)
        self._issuer = issuer
        self._audience = audience
        self._algorithms = algorithms or ["RS256"]

    def validate(self, token: str) -> dict[str, Any]:
        """Validate *token* and return the decoded JWT claims.

        Raises:
            jwt.PyJWKClientError: if the signing key cannot be resolved.
            jwt.InvalidTokenError: if the token is expired, tampered, or
                issued by a different authority.
        """
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)
        options: dict[str, Any] = {}
        decode_kwargs: dict[str, Any] = {
            "algorithms": self._algorithms,
            "issuer": self._issuer,
            "options": options,
        }
        if self._audience:
            decode_kwargs["audience"] = self._audience

        return jwt.decode(token, signing_key, **decode_kwargs)


def create_jwt_validator(keycloak_url: str, realm: str) -> JWTValidator:
    """Build a JWTValidator targeting the given Keycloak realm."""
    base = keycloak_url.rstrip("/")
    issuer = f"{base}/realms/{realm}"
    jwks_uri = f"{issuer}/protocol/openid-connect/certs"
    return JWTValidator(jwks_uri=jwks_uri, issuer=issuer)


# ---------------------------------------------------------------------------
# Protected Resource Metadata (RFC 9728)
# ---------------------------------------------------------------------------


def build_protected_resource_metadata(
    resource_uri: str,
    authorization_server: str | None,
) -> dict[str, Any]:
    """Return the OAuth 2.0 Protected Resource Metadata document.

    https://datatracker.ietf.org/doc/html/rfc9728
    """
    return {
        "resource": resource_uri,
        "authorization_servers": [authorization_server] if authorization_server else [],
        "bearer_methods_supported": ["header"],
        "resource_documentation": "https://github.com/nakamu12/lumineer",
    }
