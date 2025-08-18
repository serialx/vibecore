"""PKCE (Proof Key for Code Exchange) implementation for OAuth."""

import hashlib
import secrets
from base64 import urlsafe_b64encode

from vibecore.auth.models import PKCEChallenge


class PKCEGenerator:
    """Generates cryptographically secure PKCE challenge pairs."""

    @staticmethod
    def generate() -> PKCEChallenge:
        """
        Generate a PKCE challenge pair following RFC 7636.

        Returns:
            PKCEChallenge with verifier and challenge.
        """
        # Generate 32 bytes of random data for verifier
        verifier_bytes = secrets.token_bytes(32)
        verifier = urlsafe_b64encode(verifier_bytes).decode("ascii").rstrip("=")

        # Create SHA256 hash of verifier for challenge
        challenge_bytes = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = urlsafe_b64encode(challenge_bytes).decode("ascii").rstrip("=")

        return PKCEChallenge(verifier=verifier, challenge=challenge)
