"""
Transaction module: Data structure for blockchain transactions.

Transactions represent certificate registrations and transfers
on the blockchain, with full digital signature support.
"""

import json
import time
from hashlib import sha256
from typing import Any, Dict, Optional


class Transaction:
    """Represents a single transaction in the blockchain.

    A transaction encapsulates a certificate hash registration,
    including sender/receiver addresses, metadata, and a digital signature.

    Attributes:
        sender: Address of the transaction sender.
        recipient: Address of the transaction recipient.
        certificate_hash: Hash of the certificate being registered.
        timestamp: Unix timestamp of transaction creation.
        signature: Digital signature of the transaction.
        tx_hash: Unique hash identifier for the transaction.
        metadata: Optional dictionary of additional metadata.
    """

    def __init__(
        self,
        sender: str,
        recipient: str,
        certificate_hash: str,
        signature: str = "",
        timestamp: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a new Transaction.

        Args:
            sender: Sender's wallet address.
            recipient: Recipient's wallet address.
            certificate_hash: Hash of the certificate to register.
            signature: Digital signature (empty until signed).
            timestamp: Optional Unix timestamp.
            metadata: Optional dictionary with additional data.
        """
        self.sender = sender
        self.recipient = recipient
        self.certificate_hash = certificate_hash
        self.timestamp = timestamp or time.time()
        self.signature = signature
        self.metadata = metadata or {}
        self.tx_hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """Compute the transaction hash from its fields.

        Returns:
            Hexadecimal SHA-256 digest of the transaction data.
        """
        tx_data = {
            "sender": self.sender,
            "recipient": self.recipient,
            "certificate_hash": self.certificate_hash,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
        tx_string = json.dumps(tx_data, sort_keys=True)
        return sha256(tx_string.encode()).hexdigest()

    def sign_transaction(self, signature: str) -> None:
        """Attach a digital signature to the transaction.

        Args:
            signature: Hex-encoded digital signature string.
        """
        self.signature = signature
        self.tx_hash = self.calculate_hash()

    def is_valid(self) -> bool:
        """Validate the transaction structure.

        Checks that required fields are non-empty and that
        a signature is present.

        Returns:
            True if the transaction is structurally valid.
        """
        if not self.sender or not self.recipient:
            return False
        if not self.certificate_hash:
            return False
        if not self.signature:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the transaction to a dictionary.

        Returns:
            Dictionary representation of the transaction.
        """
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "certificate_hash": self.certificate_hash,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "tx_hash": self.tx_hash,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        """Deserialize a transaction from a dictionary.

        Args:
            data: Dictionary containing transaction fields.

        Returns:
            A new Transaction instance.
        """
        tx = cls(
            sender=data["sender"],
            recipient=data["recipient"],
            certificate_hash=data["certificate_hash"],
            signature=data.get("signature", ""),
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata", {}),
        )
        tx.tx_hash = data.get("tx_hash", tx.calculate_hash())
        return tx

    def __repr__(self) -> str:
        """Return a concise string representation."""
        return (
            f"Transaction(tx_hash={self.tx_hash[:12]}..., "
            f"cert_hash={self.certificate_hash[:12]}...)"
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on transaction hash."""
        if not isinstance(other, Transaction):
            return NotImplemented
        return self.tx_hash == other.tx_hash
