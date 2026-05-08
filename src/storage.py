"""
Storage module: Blockchain persistence to JSON files.

Handles saving and loading blockchain state, wallet data,
and certificate registries to/from disk.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from src.block import Block
from src.blockchain import Blockchain
from src.transaction import Transaction
from src.wallet import Wallet

logger = logging.getLogger(__name__)


class Storage:
    """Persistent storage for blockchain data.

    Manages JSON file I/O for blockchain state, wallets,
    and certificate records.

    Attributes:
        data_dir: Directory for storing data files.
        chain_file: Path to blockchain JSON file.
        wallet_file: Path to wallets JSON file.
    """

    def __init__(self, data_dir: str = "data") -> None:
        """Initialize storage.

        Args:
            data_dir: Directory path for data files.
        """
        self.data_dir = data_dir
        self.chain_file = os.path.join(data_dir, "chain.json")
        self.wallet_file = os.path.join(data_dir, "wallets.json")
        os.makedirs(data_dir, exist_ok=True)
        logger.debug("Storage initialized at %s", data_dir)

    def save_chain(self, blockchain: Blockchain) -> None:
        """Save blockchain to JSON file.

        Args:
            blockchain: Blockchain instance to save.
        """
        try:
            data = {
                "chain": [block.to_dict() for block in blockchain.chain],
                "pending_transactions": [
                    tx.to_dict() for tx in blockchain.pending_transactions
                ],
                "difficulty": blockchain.difficulty,
                "mining_reward": blockchain.mining_reward,
                "nodes": list(blockchain.nodes),
            }
            with open(self.chain_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Chain saved: %d blocks", len(blockchain.chain))
        except OSError as e:
            logger.error("Failed to save chain: %s", e)
            raise

    def load_chain(self) -> Blockchain:
        """Load blockchain from JSON file.

        Returns:
            Reconstructed Blockchain instance.

        Raises:
            FileNotFoundError: If no chain file exists.
        """
        if not os.path.exists(self.chain_file):
            raise FileNotFoundError(f"Chain file not found: {self.chain_file}")

        with open(self.chain_file, "r") as f:
            data = json.load(f)

        blockchain = Blockchain()
        blockchain.chain = [Block.from_dict(b) for b in data.get("chain", [])]
        blockchain.pending_transactions = [
            Transaction.from_dict(t) for t in data.get("pending_transactions", [])
        ]
        blockchain.difficulty = data.get("difficulty", blockchain.difficulty)
        blockchain.mining_reward = data.get("mining_reward", blockchain.mining_reward)
        blockchain.nodes = set(data.get("nodes", []))
        blockchain.consensus.difficulty = blockchain.difficulty

        logger.info("Chain loaded: %d blocks", len(blockchain.chain))
        return blockchain

    def chain_exists(self) -> bool:
        """Check if chain file exists.

        Returns:
            True if chain file is present.
        """
        return os.path.exists(self.chain_file)

    def save_wallets(self, wallets: Dict[str, Wallet]) -> None:
        """Save wallets to JSON file.

        Args:
            wallets: Dictionary of address -> Wallet.
        """
        try:
            data = {addr: wallet.to_dict() for addr, wallet in wallets.items()}
            with open(self.wallet_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Wallets saved: %d wallets", len(wallets))
        except OSError as e:
            logger.error("Failed to save wallets: %s", e)
            raise

    def load_wallets(self) -> Dict[str, Wallet]:
        """Load wallets from JSON file.

        Returns:
            Dictionary of address -> Wallet.
        """
        if not os.path.exists(self.wallet_file):
            return {}

        with open(self.wallet_file, "r") as f:
            data = json.load(f)

        wallets = {}
        for addr, wallet_data in data.items():
            try:
                wallets[addr] = Wallet.from_dict(wallet_data)
            except Exception as e:
                logger.warning("Failed to load wallet %s: %s", addr[:12], e)

        logger.info("Wallets loaded: %d wallets", len(wallets))
        return wallets

    def export_certificates(
        self, blockchain: Blockchain, filepath: str
    ) -> None:
        """Export all certificate transactions to a file.

        Args:
            blockchain: Blockchain to scan.
            filepath: Output file path.
        """
        certs = []
        for block in blockchain.chain:
            for tx in block.transactions:
                if isinstance(tx, dict):
                    cert_hash = tx.get("certificate_hash", "")
                    if cert_hash and cert_hash != "mining_reward":
                        certs.append({
                            "block_index": block.index,
                            "block_hash": block.hash,
                            **tx,
                        })

        with open(filepath, "w") as f:
            json.dump(certs, f, indent=2)
        logger.info("Exported %d certificates to %s", len(certs), filepath)

    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage metadata.

        Returns:
            Dictionary with file info.
        """
        info = {"data_dir": self.data_dir, "files": {}}
        for fname in ["chain.json", "wallets.json"]:
            fpath = os.path.join(self.data_dir, fname)
            if os.path.exists(fpath):
                info["files"][fname] = {
                    "size": os.path.getsize(fpath),
                    "modified": os.path.getmtime(fpath),
                }
        return info
