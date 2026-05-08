"""
Network simulation module: Multi-node blockchain network.

Simulates a decentralized network of blockchain nodes with
message propagation, consensus, and chain synchronization.
"""

import json
import logging
import random
import time
from typing import Any, Callable, Dict, List, Optional

from src.block import Block
from src.blockchain import Blockchain
from src.transaction import Transaction

logger = logging.getLogger(__name__)


class NetworkMessage:
    """Represents a message between nodes.

    Attributes:
        msg_type: Type of message (transaction, block, chain_request, etc.).
        payload: Message data dictionary.
        sender: ID of the sending node.
        timestamp: Message creation time.
    """

    def __init__(
        self,
        msg_type: str,
        payload: Dict[str, Any],
        sender: str = "",
    ) -> None:
        """Initialize a network message.

        Args:
            msg_type: Message type string.
            payload: Message data.
            sender: Sender node ID.
        """
        self.msg_type = msg_type
        self.payload = payload
        self.sender = sender
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "msg_type": self.msg_type,
            "payload": self.payload,
            "sender": self.sender,
            "timestamp": self.timestamp,
        }

    def __repr__(self) -> str:
        return f"NetworkMessage({self.msg_type}, from={self.sender[:8]})"


class Node:
    """Represents a single node in the blockchain network.

    Attributes:
        node_id: Unique identifier.
        blockchain: Local blockchain copy.
        peers: Connected peer nodes.
        message_handlers: Registered message handlers.
        is_mining: Whether the node is currently mining.
    """

    def __init__(self, node_id: str, blockchain: Optional[Blockchain] = None) -> None:
        """Initialize a network node.

        Args:
            node_id: Unique node identifier.
            blockchain: Optional blockchain instance; creates new if None.
        """
        self.node_id = node_id
        self.blockchain = blockchain or Blockchain()
        self.peers: set = set()
        self.message_handlers: List[Callable[[NetworkMessage], None]] = []
        self.is_mining = False
        self.message_log: List[NetworkMessage] = []

    def connect_peer(self, peer_id: str) -> None:
        """Connect to a peer node.

        Args:
            peer_id: ID of the peer to connect.
        """
        if peer_id != self.node_id:
            self.peers.add(peer_id)
            self.blockchain.nodes.add(peer_id)
            logger.debug("Node %s connected to peer %s", self.node_id, peer_id)

    def disconnect_peer(self, peer_id: str) -> None:
        """Disconnect from a peer.

        Args:
            peer_id: ID of peer to disconnect.
        """
        self.peers.discard(peer_id)
        self.blockchain.nodes.discard(peer_id)

    def broadcast(self, network: "Network", message: NetworkMessage) -> None:
        """Broadcast a message to all peers.

        Args:
            network: The network instance.
            message: Message to broadcast.
        """
        message.sender = self.node_id
        for peer_id in self.peers:
            network.deliver_message(peer_id, message)
        self.message_log.append(message)

    def receive_message(self, message: NetworkMessage) -> None:
        """Process a received message.

        Args:
            message: The received network message.
        """
        self.message_log.append(message)
        if message.msg_type == "transaction":
            self._handle_transaction(message)
        elif message.msg_type == "block":
            self._handle_block(message)
        elif message.msg_type == "chain_request":
            self._handle_chain_request(message)
        elif message.msg_type == "chain_response":
            self._handle_chain_response(message)
        elif message.msg_type == "ping":
            logger.debug("Node %s received ping from %s", self.node_id, message.sender)

    def _handle_transaction(self, message: NetworkMessage) -> None:
        """Handle incoming transaction message."""
        try:
            tx_data = message.payload.get("transaction")
            if tx_data:
                tx = Transaction.from_dict(tx_data)
                self.blockchain.add_transaction(tx)
                logger.info("Node %s received transaction %s", self.node_id, tx.tx_hash[:12])
        except Exception as e:
            logger.warning("Node %s failed to process transaction: %s", self.node_id, e)

    def _handle_block(self, message: NetworkMessage) -> None:
        """Handle incoming block message."""
        try:
            block_data = message.payload.get("block")
            if block_data:
                block = Block.from_dict(block_data)
                if self.blockchain.consensus.validate_block(
                    block, self.blockchain.get_latest_block()
                ):
                    self.blockchain.chain.append(block)
                    logger.info("Node %s accepted block %d", self.node_id, block.index)
        except Exception as e:
            logger.warning("Node %s failed to process block: %s", self.node_id, e)

    def _handle_chain_request(self, message: NetworkMessage) -> None:
        """Handle chain sync request."""
        pass

    def _handle_chain_response(self, message: NetworkMessage) -> None:
        """Handle incoming chain data."""
        try:
            chain_data = message.payload.get("chain")
            if chain_data:
                remote_chain = [Block.from_dict(b) for b in chain_data]
                self.blockchain.chain = self.blockchain.consensus.resolve_conflict(
                    self.blockchain.chain, remote_chain
                )
                logger.info("Node %s synchronized chain", self.node_id)
        except Exception as e:
            logger.warning("Node %s chain sync failed: %s", self.node_id, e)

    def mine_block(self, miner_address: str) -> Optional[Block]:
        """Mine the next block.

        Args:
            miner_address: Address for mining reward.

        Returns:
            The mined block, or None if no transactions.
        """
        if not self.blockchain.pending_transactions:
            logger.debug("No transactions to mine")
            return None

        self.is_mining = True
        try:
            block = self.blockchain.mine_pending_transactions(miner_address)
            return block
        finally:
            self.is_mining = False

    def get_info(self) -> Dict[str, Any]:
        """Get node information.

        Returns:
            Dictionary with node stats.
        """
        return {
            "node_id": self.node_id,
            "peers": list(self.peers),
            "block_count": len(self.blockchain.chain),
            "pending_tx": len(self.blockchain.pending_transactions),
            "is_mining": self.is_mining,
            "messages_received": len(self.message_log),
        }

    def __repr__(self) -> str:
        return (
            f"Node({self.node_id}, peers={len(self.peers)}, "
            f"blocks={len(self.blockchain.chain)})"
        )


class Network:
    """Simulates a peer-to-peer blockchain network.

    Manages nodes, message routing, and network-wide operations.

    Attributes:
        nodes: Dictionary of node_id -> Node.
        message_queue: Pending messages per node.
    """

    def __init__(self) -> None:
        """Initialize an empty network."""
        self.nodes: Dict[str, Node] = {}
        self._message_queues: Dict[str, List[NetworkMessage]] = {}

    def create_node(self, node_id: str, blockchain: Optional[Blockchain] = None) -> Node:
        """Create and register a new node.

        Args:
            node_id: Unique node identifier.
            blockchain: Optional blockchain to share.

        Returns:
            The created node.
        """
        node = Node(node_id, blockchain)
        self.nodes[node_id] = node
        self._message_queues[node_id] = []
        logger.info("Node created: %s", node_id)
        return node

    def connect_nodes(self, node_id_1: str, node_id_2: str) -> None:
        """Create a bidirectional connection between two nodes.

        Args:
            node_id_1: First node ID.
            node_id_2: Second node ID.
        """
        if node_id_1 in self.nodes and node_id_2 in self.nodes:
            self.nodes[node_id_1].connect_peer(node_id_2)
            self.nodes[node_id_2].connect_peer(node_id_1)
            logger.debug("Connected %s <-> %s", node_id_1, node_id_2)

    def deliver_message(self, node_id: str, message: NetworkMessage) -> None:
        """Deliver a message to a node's queue.

        Args:
            node_id: Target node ID.
            message: Message to deliver.
        """
        if node_id in self._message_queues:
            self._message_queues[node_id].append(message)

    def process_all_messages(self) -> int:
        """Process all queued messages across the network.

        Returns:
            Total number of messages processed.
        """
        total = 0
        for node_id, queue in self._message_queues.items():
            while queue:
                msg = queue.pop(0)
                self.nodes[node_id].receive_message(msg)
                total += 1
        return total

    def broadcast_to_all(self, sender_id: str, message: NetworkMessage) -> None:
        """Broadcast a message from a sender to all other nodes.

        Args:
            sender_id: ID of sending node.
            message: Message to broadcast.
        """
        message.sender = sender_id
        for node_id, node in self.nodes.items():
            if node_id != sender_id:
                node.receive_message(message)

    def get_network_stats(self) -> Dict[str, Any]:
        """Get statistics for the entire network.

        Returns:
            Dictionary with network-wide metrics.
        """
        return {
            "node_count": len(self.nodes),
            "total_blocks": sum(len(n.blockchain.chain) for n in self.nodes.values()),
            "total_pending_tx": sum(
                len(n.blockchain.pending_transactions) for n in self.nodes.values()
            ),
            "total_connections": sum(
                len(n.peers) for n in self.nodes.values()
            ) // 2,
        }

    def __repr__(self) -> str:
        return f"Network(nodes={len(self.nodes)})"
