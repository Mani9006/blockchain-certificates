"""Tests for the Consensus module."""

import time

import pytest

from src.block import Block
from src.consensus import Consensus


class TestConsensus:
    """Test cases for Consensus class."""

    def test_validate_block_valid(self) -> None:
        """Test validation of a valid block."""
        consensus = Consensus(difficulty=1)
        b1 = Block(index=0, transactions=[], previous_hash="0" * 64)
        b1.mine_block(1)
        b2 = Block(index=1, transactions=[], previous_hash=b1.hash)
        b2.mine_block(1)
        assert consensus.validate_block(b2, b1) is True

    def test_validate_block_wrong_index(self) -> None:
        """Test validation fails with wrong index."""
        consensus = Consensus(difficulty=1)
        b1 = Block(index=0, transactions=[], previous_hash="0" * 64)
        b1.mine_block(1)
        b2 = Block(index=5, transactions=[], previous_hash=b1.hash)
        b2.mine_block(1)
        assert consensus.validate_block(b2, b1) is False

    def test_validate_block_wrong_prev_hash(self) -> None:
        """Test validation fails with wrong previous hash."""
        consensus = Consensus(difficulty=1)
        b1 = Block(index=0, transactions=[], previous_hash="0" * 64)
        b1.mine_block(1)
        b2 = Block(index=1, transactions=[], previous_hash="wrong_hash")
        b2.mine_block(1)
        assert consensus.validate_block(b2, b1) is False

    def test_validate_block_insufficient_difficulty(self) -> None:
        """Test validation fails with insufficient difficulty."""
        consensus = Consensus(difficulty=4)
        b1 = Block(index=0, transactions=[], previous_hash="0" * 64)
        b1.mine_block(1)
        b2 = Block(index=1, transactions=[], previous_hash=b1.hash)
        b2.mine_block(1)  # Mined with difficulty 1, not 4
        assert consensus.validate_block(b2, b1) is False

    def test_validate_chain_valid(self) -> None:
        """Test validation of a valid chain."""
        consensus = Consensus(difficulty=1)
        chain = []
        genesis = Block(index=0, transactions=[], previous_hash="0" * 64)
        genesis.mine_block(1)
        chain.append(genesis)
        for i in range(1, 4):
            b = Block(index=i, transactions=[], previous_hash=chain[-1].hash)
            b.mine_block(1)
            chain.append(b)
        assert consensus.validate_chain(chain) is True

    def test_validate_empty_chain(self) -> None:
        """Test validation of empty chain."""
        consensus = Consensus()
        assert consensus.validate_chain([]) is True

    def test_validate_genesis_only(self) -> None:
        """Test validation of genesis-only chain."""
        consensus = Consensus(difficulty=1)
        genesis = Block(index=0, transactions=[], previous_hash="0" * 64)
        genesis.mine_block(1)
        assert consensus.validate_chain([genesis]) is True

    def test_validate_chain_with_tampered_block(self) -> None:
        """Test validation fails with tampered block."""
        consensus = Consensus(difficulty=1)
        chain = []
        genesis = Block(index=0, transactions=[], previous_hash="0" * 64)
        genesis.mine_block(1)
        chain.append(genesis)
        b1 = Block(index=1, transactions=[], previous_hash=genesis.hash)
        b1.mine_block(1)
        chain.append(b1)
        # Tamper with the block
        chain[1].transactions = [{"tampered": True}]
        assert consensus.validate_chain(chain) is False

    def test_tamper_check_no_tampering(self) -> None:
        """Test tamper detection on clean chain."""
        consensus = Consensus(difficulty=1)
        chain = []
        genesis = Block(index=0, transactions=[], previous_hash="0" * 64)
        genesis.mine_block(1)
        chain.append(genesis)
        for i in range(1, 4):
            b = Block(index=i, transactions=[], previous_hash=chain[-1].hash)
            b.mine_block(1)
            chain.append(b)
        tampered = consensus.tamper_check(chain)
        assert tampered == []

    def test_tamper_check_with_tampering(self) -> None:
        """Test tamper detection finds tampered blocks."""
        consensus = Consensus(difficulty=1)
        chain = []
        genesis = Block(index=0, transactions=[], previous_hash="0" * 64)
        genesis.mine_block(1)
        chain.append(genesis)
        for i in range(1, 4):
            b = Block(index=i, transactions=[], previous_hash=chain[-1].hash)
            b.mine_block(1)
            chain.append(b)
        # Tamper block 1
        chain[1].transactions = [{"tampered": True}]
        tampered = consensus.tamper_check(chain)
        assert 1 in tampered

    def test_resolve_conflict_longer_chain_wins(self) -> None:
        """Test conflict resolution picks longer valid chain."""
        consensus = Consensus(difficulty=1)
        local = []
        genesis = Block(index=0, transactions=[], previous_hash="0" * 64)
        genesis.mine_block(1)
        local.append(genesis)
        for i in range(1, 3):
            b = Block(index=i, transactions=[], previous_hash=local[-1].hash)
            b.mine_block(1)
            local.append(b)

        remote = list(local)
        for i in range(3, 6):
            b = Block(index=i, transactions=[], previous_hash=remote[-1].hash)
            b.mine_block(1)
            remote.append(b)

        result = consensus.resolve_conflict(local, remote)
        assert len(result) == len(remote)

    def test_resolve_conflict_shorter_invalid(self) -> None:
        """Test conflict resolution with shorter local valid vs longer invalid remote."""
        consensus = Consensus(difficulty=1)
        local = []
        genesis = Block(index=0, transactions=[], previous_hash="0" * 64)
        genesis.mine_block(1)
        local.append(genesis)
        for i in range(1, 3):
            b = Block(index=i, transactions=[], previous_hash=local[-1].hash)
            b.mine_block(1)
            local.append(b)

        # Create invalid remote chain
        remote = list(local)
        bad = Block(index=99, transactions=[], previous_hash="bad")
        bad.hash = bad.calculate_hash()
        remote.append(bad)

        result = consensus.resolve_conflict(local, remote)
        assert len(result) == len(local)

    def test_difficulty_adjustment(self) -> None:
        """Test difficulty adjustment."""
        consensus = Consensus(difficulty=2, adjustment_interval=2)
        chain = []
        genesis = Block(index=0, transactions=[], previous_hash="0" * 64, timestamp=0)
        genesis.mine_block(2)
        chain.append(genesis)
        for i in range(1, 4):  # Need 4 blocks total so len % 2 == 0
            b = Block(
                index=i,
                transactions=[],
                previous_hash=chain[-1].hash,
                timestamp=i * 100,
            )
            b.mine_block(2)
            chain.append(b)
        consensus.adjust_difficulty(chain)
        # Since actual time (300) >> expected (20), difficulty should decrease
        assert consensus.difficulty == 1

    def test_invalid_genesis_wrong_index(self) -> None:
        """Test validation of genesis with wrong index."""
        consensus = Consensus(difficulty=1)
        genesis = Block(index=1, transactions=[], previous_hash="0" * 64)
        genesis.mine_block(1)
        assert consensus.validate_chain([genesis]) is False

    def test_invalid_genesis_wrong_prev_hash(self) -> None:
        """Test validation of genesis with wrong previous hash."""
        consensus = Consensus(difficulty=1)
        genesis = Block(index=0, transactions=[], previous_hash="not_zeros")
        genesis.mine_block(1)
        assert consensus.validate_chain([genesis]) is False
