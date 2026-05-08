"""
CLI module: Command-line interface for blockchain certificate operations.

Provides interactive commands for wallet management, certificate
issuance/verification, mining, and blockchain exploration.
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from src.blockchain import Blockchain
from src.certificate import Certificate
from src.explorer import Explorer
from src.merkle import MerkleTree
from src.network import Network, NetworkMessage, Node
from src.storage import Storage
from src.wallet import Wallet

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class CertificateCLI:
    """Main CLI controller for the certificate blockchain."""

    def __init__(self) -> None:
        """Initialize CLI with storage and blockchain."""
        self.storage = Storage()
        self.blockchain: Optional[Blockchain] = None
        self.explorer: Optional[Explorer] = None
        self.network: Optional[Network] = None
        self.wallets: Dict[str, Wallet] = {}
        self._load_or_init()

    def _load_or_init(self) -> None:
        """Load existing chain or create new."""
        try:
            self.blockchain = self.storage.load_chain()
            logger.info("Loaded existing blockchain")
        except FileNotFoundError:
            self.blockchain = Blockchain()
            logger.info("Created new blockchain")

        self.explorer = Explorer(self.blockchain)
        self.wallets = self.storage.load_wallets()

    def _save_state(self) -> None:
        """Persist current state to disk."""
        if self.blockchain:
            self.storage.save_chain(self.blockchain)
        if self.wallets:
            self.storage.save_wallets(self.wallets)

    # ---- Wallet commands ----

    def create_wallet(self, name: str) -> Wallet:
        """Create a new wallet.

        Args:
            name: Human-readable name for the wallet.

        Returns:
            The created wallet.
        """
        wallet = Wallet()
        self.wallets[wallet.address] = wallet
        self._save_state()
        print(f"Wallet created: {name}")
        print(f"  Address: {wallet.address}")
        print(f"  Public Key: {wallet.get_public_key_pem()[:60]}...")
        return wallet

    def list_wallets(self) -> None:
        """List all wallets."""
        if not self.wallets:
            print("No wallets found.")
            return
        print(f"{'Address':<44} {'Name'}")
        print("-" * 50)
        for addr, wallet in self.wallets.items():
            name = wallet.metadata.get("name", "N/A") if hasattr(wallet, "metadata") else "N/A"
            print(f"{addr:<44} {name}")

    def get_wallet(self, address: str) -> Optional[Wallet]:
        """Get a wallet by address prefix or full address.

        Args:
            address: Wallet address (full or prefix).

        Returns:
            Wallet if found, None otherwise.
        """
        if address in self.wallets:
            return self.wallets[address]
        for addr, wallet in self.wallets.items():
            if addr.startswith(address):
                return wallet
        return None

    # ---- Certificate commands ----

    def issue_certificate(
        self,
        holder_name: str,
        course_name: str,
        issuer_address: str,
        recipient_address: str,
        grade: str = "",
        expiry_date: str = "",
    ) -> Dict[str, Any]:
        """Issue a new certificate and register on blockchain.

        Args:
            holder_name: Name of certificate holder.
            course_name: Course/qualification name.
            issuer_address: Issuer's wallet address.
            recipient_address: Recipient's wallet address.
            grade: Optional grade.
            expiry_date: Optional expiry date (ISO format).

        Returns:
            Result dictionary with certificate and transaction.
        """
        issuer_wallet = self.get_wallet(issuer_address)
        if not issuer_wallet:
            raise ValueError(f"Issuer wallet not found: {issuer_address}")

        cert = Certificate(
            holder_name=holder_name,
            issuer_name=issuer_wallet.address[:16],
            course_name=course_name,
            grade=grade,
            expiry_date=expiry_date,
        )

        tx = self.blockchain.register_certificate(
            certificate_hash=cert.cert_hash,
            issuer_wallet=issuer_wallet,
            recipient_address=recipient_address,
            metadata=cert.to_dict(),
        )

        self._save_state()
        print(f"Certificate issued to {holder_name}")
        print(f"  Cert Hash: {cert.cert_hash}")
        print(f"  TX Hash:   {tx.tx_hash}")
        print(f"  Status:    Pending (mine to confirm)")
        return {"certificate": cert.to_dict(), "transaction": tx.to_dict()}

    def verify_certificate(self, cert_hash: str) -> Dict[str, Any]:
        """Verify a certificate on the blockchain.

        Args:
            cert_hash: Hash of certificate to verify.

        Returns:
            Verification result dictionary.
        """
        result = self.blockchain.verify_certificate(cert_hash)
        if result["found"]:
            print("Certificate FOUND on blockchain")
            print(f"  Block:        #{result['block_index']}")
            print(f"  Block Hash:   {result['block_hash'][:40]}...")
            print(f"  Confirmations: {result['confirmations']}")
            tx = result["transaction"]
            if tx and tx.get("metadata"):
                meta = tx["metadata"]
                print(f"  Holder:       {meta.get('holder_name', 'N/A')}")
                print(f"  Course:       {meta.get('course_name', 'N/A')}")
                print(f"  Issuer:       {meta.get('issuer_name', 'N/A')}")
                print(f"  Issue Date:   {meta.get('issue_date', 'N/A')}")
        else:
            print("Certificate NOT FOUND on blockchain")
        return result

    def batch_verify(self, cert_hashes: List[str]) -> Dict[str, Any]:
        """Batch verify certificates using Merkle tree.

        Args:
            cert_hashes: List of certificate hashes.

        Returns:
            Result with Merkle root and individual results.
        """
        merkle_tree = MerkleTree(cert_hashes)
        results = []

        for i, cert_hash in enumerate(cert_hashes):
            block_result = self.blockchain.verify_certificate(cert_hash)
            proof = merkle_tree.get_proof(i)
            results.append({
                "cert_hash": cert_hash,
                "found": block_result["found"],
                "merkle_index": i,
                "proof": proof,
            })

        print(f"Batch verification complete")
        print(f"  Merkle Root: {merkle_tree.root}")
        print(f"  Total:       {len(cert_hashes)}")
        print(f"  Found:       {sum(1 for r in results if r['found'])}")
        print(f"  Missing:     {sum(1 for r in results if not r['found'])}")
        return {"merkle_root": merkle_tree.root, "results": results}

    # ---- Mining commands ----

    def mine(self, miner_address: str) -> None:
        """Mine pending transactions.

        Args:
            miner_address: Address for mining reward.
        """
        if not self.blockchain.pending_transactions:
            print("No pending transactions to mine.")
            return

        block = self.blockchain.mine_pending_transactions(miner_address)
        self._save_state()
        print(f"Block mined!")
        print(f"  Index:   {block.index}")
        print(f"  Hash:    {block.hash}")
        print(f"  Nonce:   {block.nonce}")
        print(f"  TXs:     {len(block.transactions)}")

    # ---- Explorer commands ----

    def show_chain(self) -> None:
        """Display blockchain summary."""
        if self.explorer:
            print(self.explorer.get_chain_summary())

    def show_block(self, index: int) -> None:
        """Display a specific block.

        Args:
            index: Block index.
        """
        if not self.explorer:
            return
        block = self.explorer.get_block_by_index(index)
        if block:
            print(self.explorer.get_block_detail(block))
        else:
            print(f"Block #{index} not found.")

    def search(self, query: str) -> None:
        """Search the blockchain.

        Args:
            query: Search string.
        """
        if not self.explorer:
            return
        results = self.explorer.search(query)
        print(f"Search results for: {query}")
        print(f"  Blocks found:       {len(results['blocks'])}")
        print(f"  Transactions found: {len(results['transactions'])}")
        for block_data in results["blocks"]:
            print(f"\n  Block #{block_data['index']} - {block_data['hash'][:32]}...")
        for tx_data in results["transactions"][:5]:
            print(f"  TX: {tx_data.get('tx_hash', 'N/A')[:32]}...")

    def validate_chain(self) -> None:
        """Validate the blockchain and report."""
        valid = self.blockchain.is_chain_valid()
        tampered = self.blockchain.get_tampered_blocks()
        print(f"Chain validation: {'VALID' if valid else 'INVALID'}")
        if tampered:
            print(f"  Tampered blocks detected at indices: {tampered}")
        else:
            print("  No tampering detected.")

    # ---- Network simulation ----

    def simulate_network(self, node_count: int = 3) -> None:
        """Create and simulate a network.

        Args:
            node_count: Number of nodes to create.
        """
        self.network = Network()
        for i in range(node_count):
            node_id = f"node_{i}"
            if i == 0:
                node = self.network.create_node(node_id, self.blockchain)
            else:
                node = self.network.create_node(node_id)

        # Connect all nodes
        node_ids = list(self.network.nodes.keys())
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                self.network.connect_nodes(node_ids[i], node_ids[j])

        print(f"Network created with {node_count} nodes")
        print(f"Connections: {self.network.get_network_stats()['total_connections']}")

    def show_stats(self) -> None:
        """Show blockchain statistics."""
        stats = self.blockchain.get_statistics()
        print(json.dumps(stats, indent=2))


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Blockchain Certificate Verification CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s wallet create --name "University"
  %(prog)s cert issue --holder "Alice" --course "CS101" --issuer <addr> --recipient <addr>
  %(prog)s cert verify --hash <cert_hash>
  %(prog)s mine --miner <addr>
  %(prog)s explorer summary
  %(prog)s explorer block --index 1
  %(prog)s chain validate
  %(prog)s network simulate --nodes 5
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Wallet commands
    wallet_parser = subparsers.add_parser("wallet", help="Wallet management")
    wallet_sub = wallet_parser.add_subparsers(dest="wallet_cmd")
    w_create = wallet_sub.add_parser("create", help="Create wallet")
    w_create.add_argument("--name", required=True, help="Wallet name")
    wallet_sub.add_parser("list", help="List wallets")

    # Certificate commands
    cert_parser = subparsers.add_parser("cert", help="Certificate operations")
    cert_sub = cert_parser.add_subparsers(dest="cert_cmd")

    c_issue = cert_sub.add_parser("issue", help="Issue certificate")
    c_issue.add_argument("--holder", required=True, help="Holder name")
    c_issue.add_argument("--course", required=True, help="Course name")
    c_issue.add_argument("--issuer", required=True, help="Issuer address")
    c_issue.add_argument("--recipient", required=True, help="Recipient address")
    c_issue.add_argument("--grade", default="", help="Grade")
    c_issue.add_argument("--expiry", default="", help="Expiry date")

    c_verify = cert_sub.add_parser("verify", help="Verify certificate")
    c_verify.add_argument("--hash", required=True, help="Certificate hash")

    c_batch = cert_sub.add_parser("batch-verify", help="Batch verify")
    c_batch.add_argument("--hashes", required=True, nargs="+", help="Certificate hashes")

    # Mining
    mine_parser = subparsers.add_parser("mine", help="Mine pending transactions")
    mine_parser.add_argument("--miner", required=True, help="Miner address")

    # Explorer
    exp_parser = subparsers.add_parser("explorer", help="Blockchain explorer")
    exp_sub = exp_parser.add_subparsers(dest="exp_cmd")
    exp_sub.add_parser("summary", help="Show summary")
    e_block = exp_sub.add_parser("block", help="Show block")
    e_block.add_argument("--index", type=int, required=True, help="Block index")
    e_search = exp_sub.add_parser("search", help="Search")
    e_search.add_argument("--query", required=True, help="Search query")

    # Chain
    chain_parser = subparsers.add_parser("chain", help="Chain operations")
    chain_sub = chain_parser.add_subparsers(dest="chain_cmd")
    chain_sub.add_parser("validate", help="Validate chain")
    chain_sub.add_parser("stats", help="Show stats")

    # Network
    net_parser = subparsers.add_parser("network", help="Network simulation")
    net_sub = net_parser.add_subparsers(dest="net_cmd")
    n_sim = net_sub.add_parser("simulate", help="Simulate network")
    n_sim.add_argument("--nodes", type=int, default=3, help="Number of nodes")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = CertificateCLI()

    try:
        if args.command == "wallet":
            if args.wallet_cmd == "create":
                cli.create_wallet(args.name)
            elif args.wallet_cmd == "list":
                cli.list_wallets()
            else:
                wallet_parser.print_help()

        elif args.command == "cert":
            if args.cert_cmd == "issue":
                cli.issue_certificate(
                    holder_name=args.holder,
                    course_name=args.course,
                    issuer_address=args.issuer,
                    recipient_address=args.recipient,
                    grade=args.grade,
                    expiry_date=args.expiry,
                )
            elif args.cert_cmd == "verify":
                cli.verify_certificate(args.hash)
            elif args.cert_cmd == "batch-verify":
                cli.batch_verify(args.hashes)
            else:
                cert_parser.print_help()

        elif args.command == "mine":
            cli.mine(args.miner)

        elif args.command == "explorer":
            if args.exp_cmd == "summary":
                cli.show_chain()
            elif args.exp_cmd == "block":
                cli.show_block(args.index)
            elif args.exp_cmd == "search":
                cli.search(args.query)
            else:
                exp_parser.print_help()

        elif args.command == "chain":
            if args.chain_cmd == "validate":
                cli.validate_chain()
            elif args.chain_cmd == "stats":
                cli.show_stats()
            else:
                chain_parser.print_help()

        elif args.command == "network":
            if args.net_cmd == "simulate":
                cli.simulate_network(args.nodes)
            else:
                net_parser.print_help()

        else:
            parser.print_help()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
