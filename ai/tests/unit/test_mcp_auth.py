"""Unit tests for MCP OAuth 2.1 JWT validation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# JWTValidator tests
# ---------------------------------------------------------------------------


class TestJWTValidator:
    """Tests for JWT token validation against Keycloak JWKS."""

    def test_validate_valid_token_returns_claims(self) -> None:
        """A valid token should return the decoded claims dict."""
        from app.interfaces.mcp.auth import JWTValidator

        mock_signing_key = MagicMock()
        mock_claims = {"sub": "user-123", "iss": "http://keycloak:8080/realms/lumineer"}

        with (
            patch("app.interfaces.mcp.auth.PyJWKClient") as mock_jwks_cls,
            patch("app.interfaces.mcp.auth.jwt") as mock_jwt,
        ):
            mock_jwks = MagicMock()
            mock_jwks.get_signing_key_from_jwt.return_value = mock_signing_key
            mock_jwks_cls.return_value = mock_jwks
            mock_jwt.decode.return_value = mock_claims

            validator = JWTValidator(
                jwks_uri="http://keycloak:8080/realms/lumineer/protocol/openid-connect/certs",
                issuer="http://keycloak:8080/realms/lumineer",
            )
            result = validator.validate("valid.jwt.token")

        assert result == mock_claims
        mock_jwt.decode.assert_called_once()

    def test_validate_invalid_token_raises(self) -> None:
        """An invalid/expired token should raise PyJWTError."""
        import jwt

        from app.interfaces.mcp.auth import JWTValidator

        with (
            patch("app.interfaces.mcp.auth.PyJWKClient") as mock_jwks_cls,
            patch("app.interfaces.mcp.auth.jwt") as mock_jwt,
        ):
            mock_jwks = MagicMock()
            mock_jwks.get_signing_key_from_jwt.return_value = MagicMock()
            mock_jwks_cls.return_value = mock_jwks
            mock_jwt.decode.side_effect = jwt.InvalidTokenError("Expired token")
            mock_jwt.InvalidTokenError = jwt.InvalidTokenError

            validator = JWTValidator(
                jwks_uri="http://keycloak:8080/realms/lumineer/protocol/openid-connect/certs",
                issuer="http://keycloak:8080/realms/lumineer",
            )

            with pytest.raises(jwt.InvalidTokenError):
                validator.validate("expired.jwt.token")

    def test_validate_unknown_key_raises(self) -> None:
        """A token signed by an unknown key should raise during JWKS lookup."""
        import jwt

        from app.interfaces.mcp.auth import JWTValidator

        with patch("app.interfaces.mcp.auth.PyJWKClient") as mock_jwks_cls:
            mock_jwks = MagicMock()
            mock_jwks.get_signing_key_from_jwt.side_effect = jwt.PyJWKClientError("Key not found")
            mock_jwks_cls.return_value = mock_jwks

            validator = JWTValidator(
                jwks_uri="http://keycloak:8080/realms/lumineer/protocol/openid-connect/certs",
                issuer="http://keycloak:8080/realms/lumineer",
            )

            with pytest.raises(jwt.PyJWKClientError):
                validator.validate("unknown.key.token")


# ---------------------------------------------------------------------------
# ProtectedResourceMetadata tests
# ---------------------------------------------------------------------------


class TestProtectedResourceMetadata:
    """Tests for the OAuth 2.1 Protected Resource Metadata helper."""

    def test_build_metadata_returns_correct_structure(self) -> None:
        """Metadata should include resource URI and authorization_servers list."""
        from app.interfaces.mcp.auth import build_protected_resource_metadata

        metadata = build_protected_resource_metadata(
            resource_uri="https://mcp.example.com",
            authorization_server="https://keycloak.example.com/realms/lumineer",
        )

        assert metadata["resource"] == "https://mcp.example.com"
        assert "authorization_servers" in metadata
        assert "https://keycloak.example.com/realms/lumineer" in metadata["authorization_servers"]

    def test_build_metadata_without_auth_server(self) -> None:
        """When no auth server configured, authorization_servers should be empty."""
        from app.interfaces.mcp.auth import build_protected_resource_metadata

        metadata = build_protected_resource_metadata(
            resource_uri="https://mcp.example.com",
            authorization_server=None,
        )

        assert metadata["resource"] == "https://mcp.example.com"
        assert metadata["authorization_servers"] == []


# ---------------------------------------------------------------------------
# KeycloakTokenVerifier tests
# ---------------------------------------------------------------------------


class TestKeycloakTokenVerifier:
    """Tests for KeycloakTokenVerifier (MCP TokenVerifier protocol)."""

    @pytest.mark.asyncio
    async def test_verify_valid_token_returns_access_token(self) -> None:
        """A valid JWT should produce an AccessToken."""
        from app.interfaces.mcp.server import KeycloakTokenVerifier

        mock_validator = MagicMock()
        mock_validator.validate.return_value = {
            "sub": "user-123",
            "azp": "mcp-client",
            "scope": "openid profile",
            "exp": 9999999999,
        }

        verifier = KeycloakTokenVerifier(jwt_validator=mock_validator)
        result = await verifier.verify_token("valid.jwt.token")

        assert result is not None
        assert result.client_id == "mcp-client"
        assert "openid" in result.scopes

    @pytest.mark.asyncio
    async def test_verify_invalid_token_returns_none(self) -> None:
        """An invalid JWT should return None (not raise)."""
        import jwt

        from app.interfaces.mcp.server import KeycloakTokenVerifier

        mock_validator = MagicMock()
        mock_validator.validate.side_effect = jwt.InvalidTokenError("bad token")

        verifier = KeycloakTokenVerifier(jwt_validator=mock_validator)
        result = await verifier.verify_token("bad.jwt.token")

        assert result is None
