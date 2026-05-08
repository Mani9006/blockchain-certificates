"""
Blockchain module: Core blockchain data structure and operations.

Manages the chain of blocks, pending transactions, mining,
certificate registration, and verification.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from src.block import Block
from src.consensus import Consensus
from src.merkle import MerkleTree
from src.transaction import Transaction
from src.wallet import Wallet

logger = logging.getLogger(__name__)


class Blockchain:
    """Core blockchain for certificate verification.

    Manages blocks, transactions, mining, and certificate
    registration/verification workflows.

    Attributes:
        chain: List of blocks in the blockchain.
        pending_transactions: Transactions waiting to be mined.
        consensus: Consensus engine instance.
        nodes: Set of known node addresses.
        difficulty: Current mining difficulty.
        mining_reward: Reward for mining a block.
    """

    def __init__(
        self,
        difficulty: int = 4,
        mining_reward: float = 10.0,
        load_from_file: Optional[str] = None,
    ) -> None:
        """Initialize the blockchain.

        Args:
            difficulty: Initial proof-of-work difficulty.
            mining_reward: Tokens awarded for mining.
            load_from_file: Path to load persisted chain from.
        """
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.consensus = Consensus(difficulty=difficulty)
        self.nodes: set = set()
        self.difficulty = difficulty
        self.mining_reward = mining_reward

        if load_from_file:
            self.load_chain(load_from_file)
        else:
            self.create_genesis_block()

    def create_genesis_block(self) -> Block:
        """Create and return the genesis block.

        Returns:
            The genesis block.
        """
        genesis = Block(
            index=0,
            transactions=[],
            previous_hash="0" * 64,
            timestamp=time.time(),
        )
        genesis.mine_block(self.difficulty)
        self.chain.append(genesis)
        logger.info("Genesis block created: %s", genesis.hash[:16])
        return genesis

    def get_latest_block(self) -> Block:
        """Get the most recent block.

        Returns:
            The last block in the chain.
        """
        return self.chain[-1]

    def add_transaction(self, transaction: Transaction) -> bool:
        """Add a transaction to the pending pool.

        Args:
            transaction: Transaction to add.

        Returns:
            True if the transaction was added.

        Raises:
            ValueError: If the transaction is invalid.
        """
        if not transaction.is_valid():
            raise ValueError("Invalid transaction: missing fields or signature")

        self.pending_transactions.append(transaction)
        logger.info("Transaction added: %s", transaction.tx_hash[:12])
        return True

    def mine_pending_transactions(self, miner_address: str) -> Block:
        """Mine a new block with all pending transactions.

        Args:
            miner_address: Address to receive mining reward.

        Returns:
            The newly mined block.
        """
        reward_tx = Transaction(
            sender="network",
            recipient=miner_address,
            certificate_hash="mining_reward",
            signature="network",
            timestamp=time.time(),
        )
        transactions_to_mine = self.pending_transactions + [reward_tx]
        tx_dicts = [tx.to_dict() for tx in transactions_to_mine]

        cert_hashes = [
            tx.certificate_hash for tx in transactions_to_mine
            if tx.certificate_hash != "mining_reward"
        ]
        merkle_root = ""
        if cert_hashes:
            merkle_tree = MerkleTree(cert_hashes)
            merkle_root = merkle_tree.root

        new_block = Block(
            index=len(self.chain),
            transactions=tx_dicts,
            previous_hash=self.get_latest_block().hash,
            merkle_root=merkle_root,
        )
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        self.pending_transactions = []

        self.consensus.adjust_difficulty(self.chain)
        self.difficulty = self.consensus.difficulty

        logger.info("Block mined: %s at index %d", new_block.hash[:16], new_block.index)
        return new_block

    def register_certificate(
        self,
        certificate_hash: str,
        issuer_wallet: Wallet,
        recipient_address: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Transaction:
        """Register a certificate hash on the blockchain.

        Args:
            certificate_hash: Hash of the certificate.
            issuer_wallet: Wallet of the issuing authority.
            recipient_address: Recipient's blockchain address.
            metadata: Optional metadata dictionary.

        Returns:
            The signed transaction.
        """
        tx = Transaction(
            sender=issuer_wallet.address,
            recipient=recipient_address,
            certificate_hash=certificate_hash,
            timestamp=time.time(),
            metadata=metadata or {},
        )
        signature = issuer_wallet.sign_transaction(tx.tx_hash)
        tx.sign_transaction(signature)
        self.add_transaction(tx)
        logger.info("Certificate registered: %s", certificate_hash[:12])
        return tx

    def verify_certificate(self, certificate_hash: str) -> Dict[str, Any]:
        """Verify a certificate exists on the blockchain.

        Searches all blocks for a transaction containing the
        given certificate hash.

        Args:
            certificate_hash: Hash of the certificate to verify.

        Returns:
            Dictionary with 'found', 'block_index', 'transaction',
            and 'confirmations'.
        """
        for block in reversed(self.chain):
            for tx_data in block.transactions:
                if isinstance(tx_data, dict):
                    if tx_data.get("certificate_hash") == certificate_hash:
                        confirmations = self.get_latest_block().index - block.index
                        return {
                            "found": True,
                            "block_index": block.index,
                            "block_hash": block.hash,
                            "transaction": tx_data,
                            "confirmations": confirmations,
                        }
        return {
            "found": False,
            "block_index": None,
            "block_hash": None,
            "transaction": None,
            "confirmations": 0,
        }

    def verify_signature(
        self, tx_data: Dict[str, Any], public_key_pem: str
    ) -> bool:
        """Verify a transaction's digital signature.

        Args:
            tx_data: Transaction dictionary with tx_hash and signature.
            public_key_pem: PEM-encoded public key of the sender.

        Returns:
            True if the signature is valid.
        """
        try:
            return Wallet.verify_signature(
                public_key_pem,
                tx_data["tx_hash"],
                tx_data["signature"],
            )
        except (KeyError, Exception):
            return False

    def is_chain_valid(self) -> bool:
        """Check if the blockchain is valid.

        Returns:
            True if the entire chain passes validation.
        """
        return self.consensus.validate_chain(self.chain)

    def get_tampered_blocks(self) -> List[int]:
        """Detect any tampered blocks.

        Returns:
            List of indices of tampered blocks.
        """
        return self.consensus.tamper_check(self.chain)

    def get_certificate_history(self, certificate_hash: str) -> List[Dict[str, Any]]:
        """Get full history for a certificate hash.

        Args:
            certificate_hash: Hash of the certificate.

        Returns:
            List of all transactions referencing this certificate.
        """
        history = []
        for block in self.chain:
            for tx_data in block.transactions:
                if isinstance(tx_data, dict):
                    if tx_data.get("certificate_hash") == certificate_hash:
                        history.append({
                            "block_index": block.index,
                            "block_hash": block.hash,
                            "transaction": tx_data,
                        })
        return history

    def get_statistics(self) -> Dict[str, Any]:
        """Get blockchain statistics.

        Returns:
            Dictionary with chain metrics.
        """
        total_tx = sum(len(b.transactions) for b in self.chain)
        cert_tx = sum(
            1
            for b in self.chain
            for tx in b.transactions
            if isinstance(tx, dict) and tx.get("certificate_hash", "") != "mining_reward"
        )
        return {
            "block_count": len(self.chain),
            "total_transactions": total_tx,
            "certificate_transactions": cert_tx,
            "pending_transactions": len(self.pending_transactions),
            "current_difficulty": self.difficulty,
            "chain_valid": self.is_chain_valid(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the blockchain to a dictionary.

        Returns:
            Dictionary with chain and metadata.
        """
        return {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
            "difficulty": self.difficulty,
            "mining_reward": self.mining_reward,
            "nodes": list(self.nodes),
        }

    def load_chain(self, filepath: str) -> None:
        """Load a blockchain from a JSON file.

        Args:
            filepath: Path to the JSON file.
        """
        import json

        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            self.chain = [Block.from_dict(b) for b in data.get("chain", [])]
            self.pending_transactions = [
                Transaction.from_dict(t) for t in data.get("pending_transactions", [])
            ]
            self.difficulty = data.get("difficulty", self.difficulty)
            self.mining_reward = data.get("mining_reward", self.mining_reward)
            self.nodes = set(data.get("nodes", []))
            self.consensus.difficulty = self.difficulty
            logger.info("Chain loaded from %s (%d blocks)", filepath, len(self.chain))
        except FileNotFoundError:
            logger.warning("Chain file not found, creating genesis block")
            self.create_genesis_block()
        except json.JSONDecodeError as e:
            logger.error("Invalid chain file: %s", e)
            self.create_genesis_block()

    def __repr__(self) -> str:
        """Concise representation."""
        return (
            f"Blockchain(blocks={len(self.chain)}, "
            f"pending_tx={len(self.pending_transactions)})"
        )
