"""Tests for the Certificate module."""

import json

import pytest

from src.certificate import Certificate


class TestCertificate:
    """Test cases for Certificate class."""

    def test_create_certificate(self) -> None:
        """Test basic certificate creation."""
        cert = Certificate(
            holder_name="Alice Smith",
            issuer_name="MIT",
            course_name="Computer Science 101",
        )
        assert cert.holder_name == "Alice Smith"
        assert cert.issuer_name == "MIT"
        assert cert.course_name == "Computer Science 101"
        assert cert.cert_id  # Auto-generated
        assert len(cert.cert_hash) == 64

    def test_cert_hash_consistency(self) -> None:
        """Test that same data produces same hash."""
        cert1 = Certificate(
            holder_name="Bob",
            issuer_name="Stanford",
            course_name="CS101",
            cert_id="test-id-123",
            issue_date="2024-01-15",
        )
        cert2 = Certificate(
            holder_name="Bob",
            issuer_name="Stanford",
            course_name="CS101",
            cert_id="test-id-123",
            issue_date="2024-01-15",
        )
        assert cert1.cert_hash == cert2.cert_hash

    def test_different_certs_different_hashes(self) -> None:
        """Test that different data produces different hashes."""
        cert1 = Certificate(holder_name="Alice", issuer_name="MIT", course_name="CS101")
        cert2 = Certificate(holder_name="Bob", issuer_name="MIT", course_name="CS101")
        assert cert1.cert_hash != cert2.cert_hash

    def test_verify_integrity_valid(self) -> None:
        """Test integrity check on unmodified certificate."""
        cert = Certificate(
            holder_name="Alice",
            issuer_name="MIT",
            course_name="CS101",
        )
        assert cert.verify_integrity() is True

    def test_verify_integrity_after_tamper(self) -> None:
        """Test integrity check detects tampering."""
        cert = Certificate(
            holder_name="Alice",
            issuer_name="MIT",
            course_name="CS101",
        )
        cert.holder_name = "Eve"
        assert cert.verify_integrity() is False

    def test_to_dict(self) -> None:
        """Test serialization."""
        cert = Certificate(
            holder_name="Alice",
            issuer_name="MIT",
            course_name="CS101",
            grade="A+",
        )
        d = cert.to_dict()
        assert d["holder_name"] == "Alice"
        assert d["issuer_name"] == "MIT"
        assert d["course_name"] == "CS101"
        assert d["grade"] == "A+"
        assert "cert_hash" in d
        assert "cert_id" in d

    def test_from_dict(self) -> None:
        """Test deserialization."""
        cert = Certificate(
            holder_name="Alice",
            issuer_name="MIT",
            course_name="CS101",
        )
        d = cert.to_dict()
        restored = Certificate.from_dict(d)
        assert restored.holder_name == cert.holder_name
        assert restored.cert_hash == cert.cert_hash
        assert restored.cert_id == cert.cert_id

    def test_certificate_with_metadata(self) -> None:
        """Test certificate with metadata."""
        cert = Certificate(
            holder_name="Alice",
            issuer_name="MIT",
            course_name="CS101",
            metadata={"department": "EECS", "level": "undergraduate"},
        )
        assert cert.metadata["department"] == "EECS"
        assert cert.metadata["level"] == "undergraduate"

    def test_equality(self) -> None:
        """Test certificate equality."""
        cert1 = Certificate(
            holder_name="Alice",
            issuer_name="MIT",
            course_name="CS101",
            cert_id="same-id",
        )
        cert2 = Certificate(
            holder_name="Alice",
            issuer_name="MIT",
            course_name="CS101",
            cert_id="same-id",
        )
        assert cert1 == cert2

    def test_repr(self) -> None:
        """Test repr."""
        cert = Certificate(
            holder_name="Alice",
            issuer_name="MIT",
            course_name="CS101",
        )
        r = repr(cert)
        assert "Certificate" in r
        assert "Alice" in r
