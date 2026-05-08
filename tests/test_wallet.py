"""Tests for the Wallet module."""

import pytest

from src.wallet import Wallet


class TestWallet:
    """Test cases for Wallet class."""

    def test_create_wallet(self) -> None:
        """Test wallet creation."""
        wallet = Wallet()
        assert wallet.address
        assert len(wallet.address) == 40  # Truncated SHA-256
        assert wallet.private_key
        assert wallet.public_key

    def test_address_consistency(self) -> None:
        """Test address derived from public key."""
        wallet = Wallet()
        address = wallet.address
        # Recreate should give same address
        pem = wallet.get_public_key_pem()
        wallet2 = Wallet(private_key=wallet.private_key)
        assert wallet2.address == address

    def test_unique_wallets(self) -> None:
        """Test different wallets have different addresses."""
        w1 = Wallet()
        w2 = Wallet()
        assert w1.address != w2.address

    def test_sign_and_verify(self) -> None:
        """Test signing and verifying data."""
        wallet = Wallet()
        data = "test data to sign"
        signature = wallet.sign_data(data)
        assert signature
        is_valid = Wallet.verify_signature(
            wallet.get_public_key_pem(), data, signature
        )
        assert is_valid is True

    def test_verify_wrong_data(self) -> None:
        """Test verification fails with wrong data."""
        wallet = Wallet()
        data = "original data"
        signature = wallet.sign_data(data)
        is_valid = Wallet.verify_signature(
            wallet.get_public_key_pem(), "tampered data", signature
        )
        assert is_valid is False

    def test_verify_wrong_key(self) -> None:
        """Test verification fails with wrong public key."""
        wallet1 = Wallet()
        wallet2 = Wallet()
        data = "test data"
        signature = wallet1.sign_data(data)
        is_valid = Wallet.verify_signature(
            wallet2.get_public_key_pem(), data, signature
        )
        assert is_valid is False

    def test_sign_transaction(self) -> None:
        """Test transaction signing."""
        wallet = Wallet()
        tx_hash = "abc123" * 8  # 64 chars
        signature = wallet.sign_transaction(tx_hash)
        assert signature
        is_valid = Wallet.verify_signature(
            wallet.get_public_key_pem(), tx_hash, signature
        )
        assert is_valid is True

    def test_serialization(self) -> None:
        """Test wallet serialization/deserialization."""
        wallet = Wallet()
        d = wallet.to_dict()
        assert "address" in d
        assert "public_key" in d
        assert "private_key" in d
        restored = Wallet.from_dict(d)
        assert restored.address == wallet.address

    def test_wallet_equality(self) -> None:
        """Test wallet equality."""
        w1 = Wallet()
        w2 = Wallet(private_key=w1.private_key)
        assert w1 == w2

    def test_wallet_inequality(self) -> None:
        """Test wallet inequality."""
        w1 = Wallet()
        w2 = Wallet()
        assert w1 != w2

    def test_repr(self) -> None:
        """Test repr."""
        wallet = Wallet()
        r = repr(wallet)
        assert "Wallet" in r

    def test_get_public_key_pem(self) -> None:
        """Test public key PEM export."""
        wallet = Wallet()
        pem = wallet.get_public_key_pem()
        assert "BEGIN PUBLIC KEY" in pem
        assert "END PUBLIC KEY" in pem

    def test_get_private_key_pem(self) -> None:
        """Test private key PEM export."""
        wallet = Wallet()
        pem = wallet.get_private_key_pem()
        assert "BEGIN PRIVATE KEY" in pem
        assert "END PRIVATE KEY" in pem
