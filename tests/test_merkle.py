"""Tests for the Merkle Tree module."""

import pytest

from src.merkle import MerkleTree


class TestMerkleTree:
    """Test cases for MerkleTree class."""

    def test_empty_tree(self) -> None:
        """Test empty Merkle tree."""
        tree = MerkleTree([])
        assert tree.root == ""
        assert tree.leaves == []

    def test_single_leaf(self) -> None:
        """Test tree with single leaf."""
        tree = MerkleTree(["hash1"])
        assert tree.root == "hash1"
        assert len(tree.leaves) == 1

    def test_two_leaves(self) -> None:
        """Test tree with two leaves."""
        tree = MerkleTree(["a", "b"])
        assert tree.root != ""
        assert tree.root != "a"
        assert len(tree.leaves) == 2

    def test_even_leaves(self) -> None:
        """Test tree with even number of leaves."""
        leaves = [f"hash_{i}" for i in range(4)]
        tree = MerkleTree(leaves)
        assert tree.root != ""
        assert len(tree.leaves) == 4

    def test_odd_leaves(self) -> None:
        """Test tree with odd number of leaves (duplicate last)."""
        leaves = [f"hash_{i}" for i in range(5)]
        tree = MerkleTree(leaves)
        assert tree.root != ""
        assert len(tree.leaves) == 5

    def test_deterministic(self) -> None:
        """Test same leaves produce same root."""
        leaves = ["a", "b", "c", "d"]
        tree1 = MerkleTree(leaves)
        tree2 = MerkleTree(leaves)
        assert tree1.root == tree2.root

    def test_different_leaves_different_root(self) -> None:
        """Test different leaves produce different roots."""
        tree1 = MerkleTree(["a", "b"])
        tree2 = MerkleTree(["a", "c"])
        assert tree1.root != tree2.root

    def test_get_proof(self) -> None:
        """Test Merkle proof generation."""
        leaves = ["a", "b", "c", "d"]
        tree = MerkleTree(leaves)
        proof = tree.get_proof(0)
        assert len(proof) > 0
        assert all("hash" in p and "direction" in p for p in proof)

    def test_verify_proof(self) -> None:
        """Test proof verification."""
        leaves = ["a", "b", "c", "d"]
        tree = MerkleTree(leaves)
        proof = tree.get_proof(0)
        valid = MerkleTree.verify_proof("a", tree.root, proof)
        assert valid is True

    def test_verify_wrong_leaf(self) -> None:
        """Test verification fails with wrong leaf."""
        leaves = ["a", "b", "c", "d"]
        tree = MerkleTree(leaves)
        proof = tree.get_proof(0)
        valid = MerkleTree.verify_proof("tampered", tree.root, proof)
        assert valid is False

    def test_verify_wrong_root(self) -> None:
        """Test verification fails with wrong root."""
        leaves = ["a", "b", "c", "d"]
        tree = MerkleTree(leaves)
        proof = tree.get_proof(0)
        valid = MerkleTree.verify_proof("a", "wrong_root", proof)
        assert valid is False

    def test_proof_for_all_leaves(self) -> None:
        """Test proof generation and verification for all leaves."""
        leaves = [f"leaf_{i}" for i in range(8)]
        tree = MerkleTree(leaves)
        for i, leaf in enumerate(leaves):
            proof = tree.get_proof(i)
            valid = MerkleTree.verify_proof(leaf, tree.root, proof)
            assert valid is True, f"Proof failed for leaf {i}"

    def test_add_leaf(self) -> None:
        """Test adding a single leaf."""
        tree = MerkleTree(["a", "b"])
        root_before = tree.root
        tree.add_leaf("c")
        assert len(tree.leaves) == 3
        assert tree.root != root_before

    def test_add_leaves(self) -> None:
        """Test adding multiple leaves."""
        tree = MerkleTree(["a"])
        tree.add_leaves(["b", "c", "d"])
        assert len(tree.leaves) == 4

    def test_to_dict(self) -> None:
        """Test serialization."""
        leaves = ["a", "b"]
        tree = MerkleTree(leaves)
        d = tree.to_dict()
        assert d["leaves"] == leaves
        assert d["root"] == tree.root
        assert d["leaf_count"] == 2

    def test_proof_index_out_of_range(self) -> None:
        """Test proof with invalid index raises error."""
        tree = MerkleTree(["a", "b"])
        with pytest.raises(IndexError):
            tree.get_proof(5)

    def test_proof_negative_index(self) -> None:
        """Test proof with negative index raises error."""
        tree = MerkleTree(["a", "b"])
        with pytest.raises(IndexError):
            tree.get_proof(-1)

    def test_tree_equality(self) -> None:
        """Test tree equality based on root."""
        tree1 = MerkleTree(["a", "b", "c"])
        tree2 = MerkleTree(["a", "b", "c"])
        assert tree1 == tree2

    def test_tree_inequality(self) -> None:
        """Test tree inequality."""
        tree1 = MerkleTree(["a", "b"])
        tree2 = MerkleTree(["a", "c"])
        assert tree1 != tree2

    def test_repr(self) -> None:
        """Test repr."""
        tree = MerkleTree(["a", "b"])
        r = repr(tree)
        assert "MerkleTree" in r
