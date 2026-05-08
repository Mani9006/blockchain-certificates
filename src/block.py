"""
Block module: Core data structure for blockchain blocks.

Each block contains an index, timestamp, transactions,
previous hash, nonce, and its own hash.
"""

import json
import time
from hashlib import sha256
from typing import Any, Dict, List, Optional


class Block:
    """Represents a single block in the blockchain.

    Attributes:
        index: Position of the block in the chain.
        timestamp: Unix timestamp of block creation.
        transactions: List of transaction dictionaries.
        previous_hash: Hash of the previous block.
        nonce: Number used for proof-of-work.
        hash: SHA-256 hash of the block.
        merkle_root: Root hash of the Merkle tree over transactions.
    """

    def __init__(
        self,
        index: int,
        transactions: List[Dict[str, Any]],
        previous_hash: str,
        nonce: int = 0,
        timestamp: Optional[float] = None,
        merkle_root: str = "",
    ) -> None:
        """Initialize a new Block.

        Args:
            index: The block's position in the chain.
            transactions: List of transactions to include.
            previous_hash: Hash of the preceding block.
            nonce: Proof-of-work nonce (default 0).
            timestamp: Optional Unix timestamp; uses current time if None.
            merkle_root: Root of the transaction Merkle tree.
        """
        self.index = index
        self.timestamp = timestamp or time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.merkle_root = merkle_root
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """Compute the SHA-256 hash of this block's contents.

        The hash is computed over the block's index, timestamp,
        transaction data, previous hash, nonce, and Merkle root.

        Returns:
            Hexadecimal string of the SHA-256 digest.
        """
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "merkle_root": self.merkle_root,
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty: int) -> None:
        """Perform proof-of-work mining for this block.

        Iterates the nonce until the block hash starts with
        the required number of leading zeros.

        Args:
            difficulty: Number of leading zero hex digits required.
        """
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the block to a dictionary.

        Returns:
            Dictionary representation of the block.
        """
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
            "merkle_root": self.merkle_root,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        """Deserialize a block from a dictionary.

        Args:
            data: Dictionary containing block fields.

        Returns:
            A new Block instance populated from the dictionary.
        """
        block = cls(
            index=data["index"],
            transactions=data["transactions"],
            previous_hash=data["previous_hash"],
            nonce=data.get("nonce", 0),
            timestamp=data.get("timestamp"),
            merkle_root=data.get("merkle_root", ""),
        )
        block.hash = data.get("hash", block.calculate_hash())
        return block

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return (
            f"Block(index={self.index}, hash={self.hash[:12]}..., "
            f"tx_count={len(self.transactions)})"
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on block hash."""
        if not isinstance(other, Block):
            return NotImplemented
        return self.hash == other.hash
