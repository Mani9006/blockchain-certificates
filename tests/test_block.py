"""Tests for the Block module."""

import json
import time

import pytest

from src.block import Block


class TestBlock:
    """Test cases for Block class."""

    def test_block_creation(self) -> None:
        """Test basic block creation."""
        block = Block(
            index=0,
            transactions=[],
            previous_hash="0" * 64,
            timestamp=time.time(),
        )
        assert block.index == 0
        assert block.transactions == []
        assert block.previous_hash == "0" * 64
        assert block.nonce == 0
        assert len(block.hash) == 64  # SHA-256 hex

    def test_block_with_transactions(self) -> None:
        """Test block with transactions."""
        tx = {"sender": "a", "recipient": "b", "cert_hash": "abc123"}
        block = Block(
            index=1,
            transactions=[tx],
            previous_hash="deadbeef" * 8,
        )
        assert block.index == 1
        assert len(block.transactions) == 1
        assert block.hash is not None

    def test_mine_block(self) -> None:
        """Test proof-of-work mining."""
        block = Block(
            index=1,
            transactions=[],
            previous_hash="0" * 64,
        )
        difficulty = 2
        block.mine_block(difficulty)
        assert block.hash.startswith("0" * difficulty)
        assert block.nonce > 0

    def test_hash_changes_with_nonce(self) -> None:
        """Test that hash changes when nonce changes."""
        block = Block(
            index=1,
            transactions=[],
            previous_hash="0" * 64,
        )
        hash1 = block.hash
        block.nonce = 42
        hash2 = block.calculate_hash()
        assert hash1 != hash2

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        block = Block(
            index=2,
            transactions=[{"key": "value"}],
            previous_hash="ab" * 32,
        )
        d = block.to_dict()
        assert d["index"] == 2
        assert d["previous_hash"] == "ab" * 32
        assert "hash" in d
        assert "timestamp" in d

    def test_from_dict(self) -> None:
        """Test deserialization from dict."""
        block = Block(
            index=3,
            transactions=[],
            previous_hash="cd" * 32,
        )
        block.mine_block(2)
        d = block.to_dict()
        restored = Block.from_dict(d)
        assert restored.index == block.index
        assert restored.hash == block.hash
        assert restored.previous_hash == block.previous_hash
        assert restored.nonce == block.nonce

    def test_genesis_block(self) -> None:
        """Test genesis block properties."""
        genesis = Block(
            index=0,
            transactions=[],
            previous_hash="0" * 64,
        )
        assert genesis.index == 0
        assert genesis.previous_hash == "0" * 64

    def test_block_equality(self) -> None:
        """Test block equality with same timestamp."""
        ts = 1700000000.0
        b1 = Block(index=1, transactions=[], previous_hash="0" * 64, timestamp=ts)
        b2 = Block(index=1, transactions=[], previous_hash="0" * 64, timestamp=ts)
        assert b1 == b2

    def test_block_inequality(self) -> None:
        """Test block inequality."""
        b1 = Block(index=1, transactions=[], previous_hash="0" * 64)
        b2 = Block(index=2, transactions=[], previous_hash="0" * 64)
        assert b1 != b2

    def test_repr(self) -> None:
        """Test repr."""
        block = Block(index=5, transactions=[{"tx": 1}], previous_hash="0" * 64)
        r = repr(block)
        assert "Block" in r
        assert "5" in r
