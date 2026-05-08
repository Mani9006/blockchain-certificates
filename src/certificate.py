"""
Certificate module: Certificate creation, hashing, and validation.

Handles the lifecycle of digital certificates, including generation
of unique certificate hashes for blockchain registration.
"""

import hashlib
import json
import time
from typing import Any, Dict, Optional


class Certificate:
    """Represents a digital certificate to be registered on the blockchain.

    Attributes:
        cert_id: Unique certificate identifier (UUID).
        holder_name: Name of the certificate holder.
        issuer_name: Name of the issuing institution.
        course_name: Name of the course/qualification.
        issue_date: Date of issuance (ISO format).
        expiry_date: Optional expiry date.
        grade: Optional grade or score.
        metadata: Additional certificate metadata.
        cert_hash: SHA-256 hash of the certificate data.
    """

    def __init__(
        self,
        holder_name: str,
        issuer_name: str,
        course_name: str,
        cert_id: str = "",
        issue_date: str = "",
        expiry_date: str = "",
        grade: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a Certificate.

        Args:
            holder_name: Name of the certificate holder.
            issuer_name: Name of the issuing institution.
            course_name: Course or qualification name.
            cert_id: Unique certificate ID; auto-generated if empty.
            issue_date: Issue date in ISO format; defaults to today.
            expiry_date: Optional expiry date.
            grade: Optional grade or classification.
            metadata: Optional additional metadata dictionary.
        """
        import uuid

        self.cert_id = cert_id or str(uuid.uuid4())
        self.holder_name = holder_name
        self.issuer_name = issuer_name
        self.course_name = course_name
        self.issue_date = issue_date or time.strftime("%Y-%m-%d")
        self.expiry_date = expiry_date
        self.grade = grade
        self.metadata = metadata or {}
        self.cert_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute a deterministic hash of the certificate.

        Returns:
            SHA-256 hex digest of the certificate data.
        """
        cert_data = {
            "cert_id": self.cert_id,
            "holder_name": self.holder_name,
            "issuer_name": self.issuer_name,
            "course_name": self.course_name,
            "issue_date": self.issue_date,
            "expiry_date": self.expiry_date,
            "grade": self.grade,
            "metadata": self.metadata,
        }
        cert_string = json.dumps(cert_data, sort_keys=True)
        return hashlib.sha256(cert_string.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify the certificate's internal hash integrity.

        Returns:
            True if the stored hash matches recomputed hash.
        """
        return self.cert_hash == self._compute_hash()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation of the certificate.
        """
        return {
            "cert_id": self.cert_id,
            "holder_name": self.holder_name,
            "issuer_name": self.issuer_name,
            "course_name": self.course_name,
            "issue_date": self.issue_date,
            "expiry_date": self.expiry_date,
            "grade": self.grade,
            "metadata": self.metadata,
            "cert_hash": self.cert_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Certificate":
        """Deserialize from dictionary.

        Args:
            data: Dictionary with certificate fields.

        Returns:
            New Certificate instance.
        """
        cert = cls(
            holder_name=data["holder_name"],
            issuer_name=data["issuer_name"],
            course_name=data["course_name"],
            cert_id=data.get("cert_id", ""),
            issue_date=data.get("issue_date", ""),
            expiry_date=data.get("expiry_date", ""),
            grade=data.get("grade", ""),
            metadata=data.get("metadata", {}),
        )
        stored_hash = data.get("cert_hash", "")
        if stored_hash:
            cert.cert_hash = stored_hash
        return cert

    def __repr__(self) -> str:
        """Concise representation."""
        return (
            f"Certificate({self.holder_name}, {self.course_name}, "
            f"hash={self.cert_hash[:12]}...)"
        )

    def __eq__(self, other: object) -> bool:
        """Equality based on cert_id and hash."""
        if not isinstance(other, Certificate):
            return NotImplemented
        return self.cert_id == other.cert_id and self.cert_hash == other.cert_hash
