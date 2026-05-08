"""
Merkle tree module: Efficient batch verification of certificates.

Builds a binary Merkle tree from certificate hashes, enabling
verification of inclusion with logarithmic proof size.
"""

import json
import math
from hashlib import sha256
from typing import Any, Dict, List, Optional, Tuple


class MerkleTree:
    """Binary Merkle tree for batch certificate verification.

    Attributes:
        leaves: List of leaf hash strings.
        levels: List of tree levels (bottom-up), each a list of hashes.
        root: The Merkle root hash.
    """

    def __init__(self, leaves: Optional[List[str]] = None) -> None:
        """Initialize a Merkle tree from leaf hashes.

        Args:
            leaves: List of hash strings to use as leaves.
        """
        self.leaves: List[str] = leaves or []
        self.levels: List[List[str]] = []
        self.root: str = ""
        if self.leaves:
            self._build_tree()

    def _hash_pair(self, left: str, right: str) -> str:
        """Hash the concatenation of two sibling hashes.

        Args:
            left: Left sibling hash.
            right: Right sibling hash.

        Returns:
            SHA-256 hash of the concatenated pair.
        """
        combined = left + right
        return sha256(combined.encode()).hexdigest()

    def _build_tree(self) -> None:
        """Construct the Merkle tree from leaves.

        Builds all levels bottom-up and computes the root.
        """
        if not self.leaves:
            self.root = ""
            self.levels = []
            return

        current_level = list(self.leaves)
        self.levels = [current_level]

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                next_level.append(self._hash_pair(left, right))
            current_level = next_level
            self.levels.append(current_level)

        self.root = current_level[0] if current_level else ""

    def add_leaf(self, leaf_hash: str) -> None:
        """Add a new leaf and rebuild the tree.

        Args:
            leaf_hash: Hash to add as a new leaf.
        """
        self.leaves.append(leaf_hash)
        self._build_tree()

    def add_leaves(self, leaf_hashes: List[str]) -> None:
        """Add multiple leaves and rebuild.

        Args:
            leaf_hashes: List of hashes to add.
        """
        self.leaves.extend(leaf_hashes)
        self._build_tree()

    def get_proof(self, index: int) -> List[Dict[str, str]]:
        """Generate a Merkle proof for a leaf at the given index.

        Args:
            index: Index of the leaf to prove.

        Returns:
            List of proof steps, each with 'hash' and 'direction'.

        Raises:
            IndexError: If index is out of range.
        """
        if index < 0 or index >= len(self.leaves):
            raise IndexError(f"Leaf index {index} out of range")

        proof = []
        for level in self.levels[:-1]:
            sibling_index = index + 1 if index % 2 == 0 else index - 1
            if sibling_index < len(level):
                direction = "right" if index % 2 == 0 else "left"
                proof.append({"hash": level[sibling_index], "direction": direction})
            index //= 2

        return proof

    @staticmethod
    def verify_proof(
        leaf_hash: str, root: str, proof: List[Dict[str, str]]
    ) -> bool:
        """Verify a Merkle proof for a leaf.

        Args:
            leaf_hash: The leaf hash to verify.
            root: Expected Merkle root.
            proof: List of proof steps from get_proof().

        Returns:
            True if the proof is valid.
        """
        current = leaf_hash
        for step in proof:
            sibling = step["hash"]
            if step["direction"] == "right":
                current = sha256((current + sibling).encode()).hexdigest()
            else:
                current = sha256((sibling + current).encode()).hexdigest()
        return current == root

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary with leaves and root.
        """
        return {
            "leaves": self.leaves,
            "root": self.root,
            "leaf_count": len(self.leaves),
        }

    def __repr__(self) -> str:
        """Return a concise representation."""
        return f"MerkleTree(leaves={len(self.leaves)}, root={self.root[:16]}...)"

    def __eq__(self, other: object) -> bool:
        """Check equality based on root hash."""
        if not isinstance(other, MerkleTree):
            return NotImplemented
        return self.root == other.root
