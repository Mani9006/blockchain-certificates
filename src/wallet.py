"""
Wallet module: RSA key pair generation and digital signatures.

Provides wallet creation, address derivation, transaction signing,
and signature verification using RSA cryptography.
"""

import base64
import hashlib
import json
import logging
import os
from typing import Dict, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

logger = logging.getLogger(__name__)


class Wallet:
    """Represents a blockchain wallet with RSA key pair.

    Attributes:
        private_key: RSA private key instance.
        public_key: RSA public key instance.
        address: Blockchain address derived from public key.
    """

    def __init__(self, private_key: Optional[RSAPrivateKey] = None) -> None:
        """Initialize a wallet, generating keys if not provided.

        Args:
            private_key: Optional existing RSA private key.
        """
        if private_key:
            self.private_key = private_key
            self.public_key = private_key.public_key()
        else:
            self.private_key, self.public_key = self._generate_keypair()
        self.address = self._derive_address()

    @staticmethod
    def _generate_keypair() -> Tuple[RSAPrivateKey, RSAPublicKey]:
        """Generate a new 2048-bit RSA key pair.

        Returns:
            Tuple of (private_key, public_key).
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        return private_key, private_key.public_key()

    def _derive_address(self) -> str:
        """Derive a blockchain address from the public key.

        The address is computed as a SHA-256 digest of the
        PEM-encoded public key, truncated for readability.

        Returns:
            Hexadecimal address string.
        """
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return hashlib.sha256(pem).hexdigest()[:40]

    def sign_data(self, data: str) -> str:
        """Sign arbitrary data with the private key.

        Args:
            data: String data to sign.

        Returns:
            Base64-encoded signature string.
        """
        signature = self.private_key.sign(
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode()

    def sign_transaction(self, transaction_hash: str) -> str:
        """Sign a transaction hash.

        Args:
            transaction_hash: The hash of the transaction to sign.

        Returns:
            Base64-encoded signature string.
        """
        return self.sign_data(transaction_hash)

    @staticmethod
    def verify_signature(
        public_key_pem: str, data: str, signature: str
    ) -> bool:
        """Verify a signature against data using a public key.

        Args:
            public_key_pem: PEM-encoded public key string.
            data: Original signed data.
            signature: Base64-encoded signature.

        Returns:
            True if the signature is valid.
        """
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode()
            )
            public_key.verify(
                base64.b64decode(signature.encode()),
                data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except (InvalidSignature, Exception):
            return False

    def get_public_key_pem(self) -> str:
        """Get the PEM-encoded public key.

        Returns:
            PEM string of the public key.
        """
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    def get_private_key_pem(self) -> str:
        """Get the PEM-encoded private key.

        Returns:
            PEM string of the private key.
        """
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

    def to_dict(self) -> Dict[str, str]:
        """Serialize wallet to dictionary (for storage).

        Returns:
            Dictionary with address and keys.
        """
        return {
            "address": self.address,
            "public_key": self.get_public_key_pem(),
            "private_key": self.get_private_key_pem(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Wallet":
        """Load wallet from dictionary.

        Args:
            data: Dictionary with 'private_key' PEM string.

        Returns:
            Reconstructed Wallet instance.
        """
        private_key = serialization.load_pem_private_key(
            data["private_key"].encode(),
            password=None,
        )
        return cls(private_key=private_key)

    def __repr__(self) -> str:
        """Return a concise representation."""
        return f"Wallet(address={self.address[:16]}...)"

    def __eq__(self, other: object) -> bool:
        """Check equality based on address."""
        if not isinstance(other, Wallet):
            return NotImplemented
        return self.address == other.address
