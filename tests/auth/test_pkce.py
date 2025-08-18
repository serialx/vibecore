"""Tests for PKCE generation."""

import base64
import hashlib

from vibecore.auth.pkce import PKCEGenerator


class TestPKCEGenerator:
    """Test PKCE challenge generation."""

    def test_generate_creates_valid_pkce(self):
        """Test that PKCE generation creates valid verifier and challenge."""
        pkce = PKCEGenerator.generate()

        # Check verifier exists and has minimum length (43 chars for base64url of 32 bytes)
        assert pkce.verifier
        assert len(pkce.verifier) >= 43

        # Check challenge exists and has minimum length
        assert pkce.challenge
        assert len(pkce.challenge) >= 43

        # Verify challenge is SHA256 of verifier
        expected_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(pkce.verifier.encode("ascii")).digest()).decode("ascii").rstrip("=")
        )

        assert pkce.challenge == expected_challenge

    def test_generate_creates_unique_values(self):
        """Test that each generation creates unique values."""
        pkce1 = PKCEGenerator.generate()
        pkce2 = PKCEGenerator.generate()

        # Verifiers should be different
        assert pkce1.verifier != pkce2.verifier

        # Challenges should be different
        assert pkce1.challenge != pkce2.challenge

    def test_verifier_format(self):
        """Test that verifier uses proper base64url format."""
        pkce = PKCEGenerator.generate()

        # Should not contain standard base64 characters
        assert "+" not in pkce.verifier
        assert "/" not in pkce.verifier
        assert "=" not in pkce.verifier  # Padding should be stripped

        # Should only contain base64url characters
        import string

        allowed_chars = string.ascii_letters + string.digits + "-_"
        assert all(c in allowed_chars for c in pkce.verifier)

    def test_challenge_format(self):
        """Test that challenge uses proper base64url format."""
        pkce = PKCEGenerator.generate()

        # Should not contain standard base64 characters
        assert "+" not in pkce.challenge
        assert "/" not in pkce.challenge
        assert "=" not in pkce.challenge  # Padding should be stripped

        # Should only contain base64url characters
        import string

        allowed_chars = string.ascii_letters + string.digits + "-_"
        assert all(c in allowed_chars for c in pkce.challenge)
