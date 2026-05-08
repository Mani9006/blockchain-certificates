"""
Consensus module: Proof-of-Work and chain validation.

Provides consensus algorithms for the blockchain, including
proof-of-work difficulty adjustment and chain integrity validation.
"""

import logging
from typing import Any, Dict, List

from src.block import Block

logger = logging.getLogger(__name__)


class Consensus:
    """Proof-of-Work consensus engine.

    Manages difficulty adjustment, block validation, and
    chain integrity verification.

    Attributes:
        difficulty: Current mining difficulty (leading zeros).
        target_block_time: Target time between blocks in seconds.
        adjustment_interval: Blocks between difficulty adjustments.
    """

    def __init__(
        self,
        difficulty: int = 4,
        target_block_time: float = 10.0,
        adjustment_interval: int = 10,
    ) -> None:
        """Initialize consensus engine.

        Args:
            difficulty: Initial difficulty level.
            target_block_time: Target block interval in seconds.
            adjustment_interval: Blocks between difficulty adjustments.
        """
        self.difficulty = difficulty
        self.target_block_time = target_block_time
        self.adjustment_interval = adjustment_interval

    def validate_block(self, block: Block, previous_block: Block) -> bool:
        """Validate a single block against the previous one.

        Checks:
        - Index continuity
        - Previous hash link
        - Hash meets difficulty target
        - Hash integrity

        Args:
            block: Block to validate.
            previous_block: The preceding block in the chain.

        Returns:
            True if the block is valid.
        """
        if block.index != previous_block.index + 1:
            logger.debug("Invalid block index: %d vs %d", block.index, previous_block.index + 1)
            return False

        if block.previous_hash != previous_block.hash:
            logger.debug("Invalid previous hash link")
            return False

        target = "0" * self.difficulty
        if not block.hash.startswith(target):
            logger.debug("Block hash does not meet difficulty target")
            return False

        if block.hash != block.calculate_hash():
            logger.debug("Block hash integrity check failed")
            return False

        return True

    def validate_chain(self, chain: List[Block]) -> bool:
        """Validate an entire blockchain.

        Verifies the genesis block and all subsequent blocks.

        Args:
            chain: List of blocks to validate.

        Returns:
            True if the entire chain is valid.
        """
        if len(chain) == 0:
            return True

        if len(chain) == 1:
            genesis = chain[0]
            if genesis.index != 0:
                logger.debug("Genesis block must have index 0")
                return False
            if genesis.previous_hash != "0" * 64:
                logger.debug("Genesis block previous hash must be zeros")
                return False
            target = "0" * self.difficulty
            if not genesis.hash.startswith(target):
                logger.debug("Genesis block hash does not meet difficulty")
                return False
            return True

        for i in range(1, len(chain)):
            if not self.validate_block(chain[i], chain[i - 1]):
                logger.debug("Chain validation failed at block %d", i)
                return False

        return True

    def adjust_difficulty(self, chain: List[Block]) -> None:
        """Adjust mining difficulty based on block times.

        Recalculates difficulty every adjustment_interval blocks
        to maintain the target block time.

        Args:
            chain: Current blockchain.
        """
        if len(chain) < self.adjustment_interval + 1:
            return

        if len(chain) % self.adjustment_interval != 0:
            return

        start_idx = len(chain) - self.adjustment_interval
        start_time = chain[start_idx].timestamp
        end_time = chain[-1].timestamp
        actual_time = end_time - start_time

        expected_time = self.target_block_time * self.adjustment_interval

        if actual_time == 0:
            return

        ratio = expected_time / actual_time
        if ratio > 1.5:
            self.difficulty += 1
            logger.info("Difficulty increased to %d", self.difficulty)
        elif ratio < 0.5 and self.difficulty > 1:
            self.difficulty -= 1
            logger.info("Difficulty decreased to %d", self.difficulty)

    def resolve_conflict(
        self, local_chain: List[Block], remote_chain: List[Block]
    ) -> List[Block]:
        """Resolve chain conflicts via longest valid chain rule.

        Args:
            local_chain: Local copy of the blockchain.
            remote_chain: Remote chain received from another node.

        Returns:
            The accepted chain (longer valid one).
        """
        local_valid = self.validate_chain(local_chain)
        remote_valid = self.validate_chain(remote_chain)

        if not local_valid and not remote_valid:
            logger.warning("Both chains invalid, keeping local")
            return local_chain

        if local_valid and not remote_valid:
            return local_chain

        if remote_valid and not local_valid:
            logger.info("Replacing with valid remote chain")
            return remote_chain

        if len(remote_chain) > len(local_chain):
            logger.info("Remote chain is longer (%d vs %d)", len(remote_chain), len(local_chain))
            return remote_chain

        return local_chain

    def tamper_check(self, chain: List[Block]) -> List[int]:
        """Detect tampered blocks in the chain.

        Args:
            chain: Blockchain to check.

        Returns:
            List of indices of tampered blocks.
        """
        tampered = []

        if not chain:
            return tampered

        for i, block in enumerate(chain):
            if i == 0:
                if block.previous_hash != "0" * 64:
                    tampered.append(i)
                continue

            if block.index != i:
                tampered.append(i)

            if block.previous_hash != chain[i - 1].hash:
                tampered.append(i)

            if block.hash != block.calculate_hash():
                tampered.append(i)

        return list(set(sorted(tampered)))
