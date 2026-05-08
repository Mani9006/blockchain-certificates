"""
Explorer module: CLI-based blockchain explorer.

Provides utilities to browse, search, and inspect the blockchain,
including blocks, transactions, and certificates.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.block import Block
from src.blockchain import Blockchain


class Explorer:
    """Blockchain explorer for viewing and searching chain data.

    Attributes:
        blockchain: The blockchain to explore.
    """

    def __init__(self, blockchain: Blockchain) -> None:
        """Initialize explorer.

        Args:
            blockchain: Blockchain instance to explore.
        """
        self.blockchain = blockchain

    def get_block_by_index(self, index: int) -> Optional[Block]:
        """Find a block by its index.

        Args:
            index: Block index to search.

        Returns:
            The block if found, None otherwise.
        """
        for block in self.blockchain.chain:
            if block.index == index:
                return block
        return None

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """Find a block by its hash.

        Args:
            block_hash: Full or partial hash to search.

        Returns:
            The block if found, None otherwise.
        """
        for block in self.blockchain.chain:
            if block.hash == block_hash or block.hash.startswith(block_hash):
                return block
        return None

    def search_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Search for a transaction by hash.

        Args:
            tx_hash: Transaction hash (full or prefix).

        Returns:
            Dictionary with block and transaction info if found.
        """
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if isinstance(tx, dict):
                    tx_h = tx.get("tx_hash", "")
                    if tx_h == tx_hash or tx_h.startswith(tx_hash):
                        return {"block": block.to_dict(), "transaction": tx}
        return None

    def get_latest_blocks(self, count: int = 5) -> List[Block]:
        """Get the most recent blocks.

        Args:
            count: Number of blocks to return.

        Returns:
            List of blocks in reverse order.
        """
        return list(reversed(self.blockchain.chain[-count:]))

    def get_all_transactions(self) -> List[Dict[str, Any]]:
        """Get all transactions across all blocks.

        Returns:
            List of transaction dictionaries with block info.
        """
        transactions = []
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if isinstance(tx, dict):
                    transactions.append({
                        "block_index": block.index,
                        "block_hash": block.hash,
                        **tx,
                    })
        return transactions

    def get_address_transactions(self, address: str) -> List[Dict[str, Any]]:
        """Get all transactions for a given address.

        Args:
            address: Wallet address to filter by.

        Returns:
            List of matching transactions.
        """
        results = []
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if isinstance(tx, dict):
                    if tx.get("sender") == address or tx.get("recipient") == address:
                        results.append({
                            "block_index": block.index,
                            "block_hash": block.hash,
                            **tx,
                        })
        return results

    def get_chain_summary(self) -> str:
        """Get a formatted summary of the blockchain.

        Returns:
            Multi-line string with chain overview.
        """
        stats = self.blockchain.get_statistics()
        latest = self.blockchain.get_latest_block()

        lines = [
            "=" * 50,
            "  BLOCKCHAIN EXPLORER SUMMARY",
            "=" * 50,
            f"  Total Blocks:        {stats['block_count']}",
            f"  Total Transactions:  {stats['total_transactions']}",
            f"  Certificate TX:      {stats['certificate_transactions']}",
            f"  Pending TX:          {stats['pending_transactions']}",
            f"  Current Difficulty:  {stats['current_difficulty']}",
            f"  Chain Valid:         {'Yes' if stats['chain_valid'] else 'No'}",
            "-" * 50,
            f"  Latest Block Index:  {latest.index}",
            f"  Latest Block Hash:   {latest.hash[:32]}...",
            f"  Latest Block Time:   {self._format_time(latest.timestamp)}",
            f"  Latest Block TXs:    {len(latest.transactions)}",
            "=" * 50,
        ]
        return "\n".join(lines)

    def get_block_detail(self, block: Block) -> str:
        """Get formatted details for a block.

        Args:
            block: Block to display.

        Returns:
            Multi-line string with block details.
        """
        lines = [
            "-" * 50,
            f"  BLOCK #{block.index}",
            "-" * 50,
            f"  Hash:        {block.hash}",
            f"  Previous:    {block.previous_hash}",
            f"  Merkle Root: {block.merkle_root or 'N/A'}",
            f"  Timestamp:   {self._format_time(block.timestamp)}",
            f"  Nonce:       {block.nonce}",
            f"  TX Count:    {len(block.transactions)}",
            "-" * 50,
        ]

        for i, tx in enumerate(block.transactions):
            if isinstance(tx, dict):
                cert_hash = tx.get("certificate_hash", "")
                tx_type = "CERT" if cert_hash and cert_hash != "mining_reward" else "REWARD"
                lines.append(f"  TX [{i}] ({tx_type}):")
                lines.append(f"    Hash:   {tx.get('tx_hash', 'N/A')[:40]}...")
                lines.append(f"    From:   {tx.get('sender', 'N/A')[:20]}...")
                lines.append(f"    To:     {tx.get('recipient', 'N/A')[:20]}...")
                lines.append(f"    Cert:   {cert_hash[:40] if cert_hash else 'N/A'}")
                if tx.get("metadata"):
                    lines.append(f"    Meta:   {json.dumps(tx['metadata'])}")
            else:
                lines.append(f"  TX [{i}]: {str(tx)[:60]}")
            if i < len(block.transactions) - 1:
                lines.append("")

        lines.append("-" * 50)
        return "\n".join(lines)

    def search(self, query: str) -> Dict[str, Any]:
        """General search across the blockchain.

        Searches for blocks (by index or hash) and transactions.

        Args:
            query: Search query string.

        Returns:
            Dictionary with search results.
        """
        results: Dict[str, Any] = {
            "query": query,
            "blocks": [],
            "transactions": [],
        }

        # Try as block index
        try:
            idx = int(query)
            block = self.get_block_by_index(idx)
            if block:
                results["blocks"].append(block.to_dict())
        except ValueError:
            pass

        # Try as block hash
        if not results["blocks"]:
            block = self.get_block_by_hash(query)
            if block:
                results["blocks"].append(block.to_dict())

        # Search transactions
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if isinstance(tx, dict):
                    for value in tx.values():
                        if query in str(value):
                            results["transactions"].append({
                                "block_index": block.index,
                                "block_hash": block.hash,
                                **tx,
                            })
                            break

        return results

    @staticmethod
    def _format_time(timestamp: float) -> str:
        """Format a Unix timestamp to readable string.

        Args:
            timestamp: Unix timestamp.

        Returns:
            Formatted date-time string.
        """
        try:
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except (OSError, ValueError):
            return str(timestamp)

    def __repr__(self) -> str:
        return f"Explorer(blocks={len(self.blockchain.chain)})"
