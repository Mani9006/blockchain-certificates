"""Tests for the Blockchain module."""

import os
import tempfile

import pytest

from src.blockchain import Blockchain
from src.certificate import Certificate
from src.transaction import Transaction
from src.wallet import Wallet


class TestBlockchain:
    """Test cases for Blockchain class."""

    def test_create_blockchain(self) -> None:
        """Test blockchain creation."""
        chain = Blockchain()
        assert len(chain.chain) == 1  # Genesis
        assert chain.pending_transactions == []
        assert chain.difficulty == 4

    def test_genesis_block(self) -> None:
        """Test genesis block properties."""
        chain = Blockchain()
        genesis = chain.chain[0]
        assert genesis.index == 0
        assert genesis.previous_hash == "0" * 64

    def test_get_latest_block(self) -> None:
        """Test getting latest block."""
        chain = Blockchain()
        latest = chain.get_latest_block()
        assert latest.index == 0

    def test_add_transaction(self) -> None:
        """Test adding a transaction."""
        chain = Blockchain()
        wallet = Wallet()
        tx = Transaction(
            sender=wallet.address,
            recipient="recipient_addr",
            certificate_hash="cert_hash_123",
            signature=wallet.sign_data("cert_hash_123"),
        )
        result = chain.add_transaction(tx)
        assert result is True
        assert len(chain.pending_transactions) == 1

    def test_add_invalid_transaction(self) -> None:
        """Test adding invalid transaction raises error."""
        chain = Blockchain()
        tx = Transaction(
            sender="",
            recipient="",
            certificate_hash="",
        )
        with pytest.raises(ValueError):
            chain.add_transaction(tx)

    def test_mine_block(self) -> None:
        """Test mining a block."""
        chain = Blockchain(difficulty=1)
        wallet = Wallet()
        tx = Transaction(
            sender=wallet.address,
            recipient="recipient",
            certificate_hash="cert_hash",
            signature=wallet.sign_data("cert_hash"),
        )
        chain.add_transaction(tx)
        block = chain.mine_pending_transactions(wallet.address)
        assert block.index == 1
        assert len(block.transactions) == 2  # Original + reward
        assert len(chain.pending_transactions) == 0

    def test_mine_with_no_transactions(self) -> None:
        """Test mining with no transactions still creates block."""
        chain = Blockchain(difficulty=1)
        wallet = Wallet()
        block = chain.mine_pending_transactions(wallet.address)
        assert block is not None
        assert block.index == 1

    def test_chain_validity(self) -> None:
        """Test chain is valid after mining."""
        chain = Blockchain(difficulty=1)
        wallet = Wallet()
        tx = Transaction(
            sender=wallet.address,
            recipient="recipient",
            certificate_hash="cert_hash",
            signature=wallet.sign_data("cert_hash"),
        )
        chain.add_transaction(tx)
        chain.mine_pending_transactions(wallet.address)
        assert chain.is_chain_valid() is True

    def test_register_certificate(self) -> None:
        """Test certificate registration."""
        chain = Blockchain()
        issuer = Wallet()
        recipient = Wallet()
        cert = Certificate(
            holder_name="Alice",
            issuer_name="MIT",
            course_name="CS101",
        )
        tx = chain.register_certificate(
            certificate_hash=cert.cert_hash,
            issuer_wallet=issuer,
            recipient_address=recipient.address,
            metadata=cert.to_dict(),
        )
        assert tx.certificate_hash == cert.cert_hash
        assert len(chain.pending_transactions) == 1

    def test_verify_certificate_found(self) -> None:
        """Test verifying a registered certificate."""
        chain = Blockchain(difficulty=1)
        issuer = Wallet()
        recipient = Wallet()
        cert = Certificate(
            holder_name="Alice",
            issuer_name="MIT",
            course_name="CS101",
        )
        chain.register_certificate(
            certificate_hash=cert.cert_hash,
            issuer_wallet=issuer,
            recipient_address=recipient.address,
        )
        chain.mine_pending_transactions(issuer.address)
        result = chain.verify_certificate(cert.cert_hash)
        assert result["found"] is True
        assert result["block_index"] == 1
        assert result["confirmations"] == 0

    def test_verify_certificate_not_found(self) -> None:
        """Test verifying a non-existent certificate."""
        chain = Blockchain()
        result = chain.verify_certificate("nonexistent")
        assert result["found"] is False

    def test_tamper_detection(self) -> None:
        """Test tamper detection."""
        chain = Blockchain(difficulty=1)
        wallet = Wallet()
        tx = Transaction(
            sender=wallet.address,
            recipient="recipient",
            certificate_hash="cert_hash",
            signature=wallet.sign_data("cert_hash"),
        )
        chain.add_transaction(tx)
        chain.mine_pending_transactions(wallet.address)
        # Tamper
        chain.chain[1].transactions = [{"tampered": True}]
        tampered = chain.get_tampered_blocks()
        assert 1 in tampered

    def test_get_certificate_history(self) -> None:
        """Test getting certificate history."""
        chain = Blockchain(difficulty=1)
        issuer = Wallet()
        recipient = Wallet()
        cert = Certificate(
            holder_name="Alice",
            issuer_name="MIT",
            course_name="CS101",
        )
        chain.register_certificate(
            certificate_hash=cert.cert_hash,
            issuer_wallet=issuer,
            recipient_address=recipient.address,
        )
        chain.mine_pending_transactions(issuer.address)
        history = chain.get_certificate_history(cert.cert_hash)
        assert len(history) == 1

    def test_get_statistics(self) -> None:
        """Test getting blockchain statistics."""
        chain = Blockchain(difficulty=1)
        wallet = Wallet()
        tx = Transaction(
            sender=wallet.address,
            recipient="recipient",
            certificate_hash="cert_hash",
            signature=wallet.sign_data("cert_hash"),
        )
        chain.add_transaction(tx)
        chain.mine_pending_transactions(wallet.address)
        stats = chain.get_statistics()
        assert stats["block_count"] == 2
        assert stats["total_transactions"] == 2  # 1 cert tx + 1 reward tx in mined block
        assert stats["chain_valid"] is True

    def test_persistence(self) -> None:
        """Test saving and loading chain."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "chain.json")
            chain = Blockchain(difficulty=1)
            wallet = Wallet()
            tx = Transaction(
                sender=wallet.address,
                recipient="recipient",
                certificate_hash="cert_hash",
                signature=wallet.sign_data("cert_hash"),
            )
            chain.add_transaction(tx)
            chain.mine_pending_transactions(wallet.address)
            # Save
            chain.to_dict()
            import json

            with open(filepath, "w") as f:
                json.dump(chain.to_dict(), f)
            # Load
            chain2 = Blockchain(load_from_file=filepath)
            assert len(chain2.chain) == 2
            assert chain2.is_chain_valid() is True

    def test_multiple_blocks(self) -> None:
        """Test mining multiple blocks."""
        chain = Blockchain(difficulty=1)
        wallet = Wallet()
        for i in range(3):
            tx = Transaction(
                sender=wallet.address,
                recipient=f"recipient_{i}",
                certificate_hash=f"cert_{i}",
                signature=wallet.sign_data(f"cert_{i}"),
            )
            chain.add_transaction(tx)
            chain.mine_pending_transactions(wallet.address)
        assert len(chain.chain) == 4  # genesis + 3

    def test_chain_equality(self) -> None:
        """Test chain equality."""
        chain1 = Blockchain()
        chain2 = Blockchain()
        assert len(chain1.chain) == len(chain2.chain)

    def test_repr(self) -> None:
        """Test repr."""
        chain = Blockchain()
        r = repr(chain)
        assert "Blockchain" in r
