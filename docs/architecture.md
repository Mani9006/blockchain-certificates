# Architecture Overview

## Blockchain Certificate Verification System

### System Architecture

```
+-------------------+     +-------------------+     +-------------------+
|      CLI Layer    |     |   Explorer Layer  |     |   Network Layer   |
|      (cli.py)     |     |  (explorer.py)    |     |  (network.py)     |
+-------------------+     +-------------------+     +-------------------+
          |                        |                        |
          v                        v                        v
+-------------------+     +-------------------+     +-------------------+
|   Blockchain      |<--->|    Storage        |<--->|    Consensus      |
|   (blockchain.py) |     |    (storage.py)   |     |    (consensus.py) |
+-------------------+     +-------------------+     +-------------------+
          |
          v
+-------------------+     +-------------------+     +-------------------+
|     Block         |     |  Transaction      |     |    Certificate    |
|    (block.py)     |     |  (transaction.py) |     |  (certificate.py) |
+-------------------+     +-------------------+     +-------------------+
          |                        |
          v                        v
+-------------------+     +-------------------+     +-------------------+
|    Merkle Tree    |     |     Wallet        |     |     Node          |
|    (merkle.py)    |     |    (wallet.py)    |     |   (network.py)    |
+-------------------+     +-------------------+     +-------------------+
```

### Component Details

#### 1. Block (`block.py`)

The fundamental unit of the blockchain. Each block contains:
- **index**: Sequential position in the chain
- **timestamp**: Unix timestamp of creation
- **transactions**: List of certificate registration transactions
- **previous_hash**: Hash of the preceding block (chain linkage)
- **nonce**: Counter for proof-of-work
- **hash**: SHA-256 digest of all block contents
- **merkle_root**: Root of the transaction Merkle tree

**Key operations:**
- `calculate_hash()`: Deterministic hash computation
- `mine_block(difficulty)`: Proof-of-work mining loop

#### 2. Transaction (`transaction.py`)

Represents a certificate registration on the chain:
- **sender**: Issuer's blockchain address
- **recipient**: Holder's blockchain address
- **certificate_hash**: SHA-256 hash of certificate data
- **signature**: RSA digital signature
- **tx_hash**: Unique identifier for the transaction
- **metadata**: Additional certificate attributes

#### 3. Blockchain (`blockchain.py`)

Core orchestrator managing the entire chain:
- Chain storage and validation
- Transaction pool management
- Mining and block creation
- Certificate registration/verification
- Merkle root computation for blocks

#### 4. Wallet (`wallet.py`)

RSA-based cryptographic identity:
- 2048-bit RSA key pair generation
- Address derivation from public key
- Transaction signing with PSS padding
- Signature verification

#### 5. Consensus (`consensus.py`)

Proof-of-Work consensus engine:
- Block validation (index, previous hash, difficulty)
- Chain integrity verification
- Difficulty adjustment algorithm
- Longest-chain conflict resolution
- Tamper detection

#### 6. Merkle Tree (`merkle.py`)

Binary Merkle tree for batch verification:
- Tree construction from leaf hashes
- Proof generation for individual leaves
- Proof verification
- Efficient O(log n) inclusion verification

#### 7. Network (`network.py`)

Simulated peer-to-peer network:
- Node creation and peer connections
- Message routing and propagation
- Transaction broadcast
- Chain synchronization
- Conflict resolution across nodes

#### 8. Storage (`storage.py`)

JSON-based persistence layer:
- Blockchain serialization/deserialization
- Wallet storage
- Certificate export
- Storage metadata

#### 9. Explorer (`explorer.py`)

Chain inspection and search:
- Block lookup by index or hash
- Transaction search
- Address transaction history
- Formatted chain summaries

### Data Flow

```
1. Certificate Issuance:
   Issuer -> Create Certificate -> Compute Hash
   -> Create Transaction -> Sign with Private Key
   -> Add to Pending Pool -> Mine Block
   -> Broadcast to Network

2. Certificate Verification:
   Verifier -> Enter Certificate Hash
   -> Search Blockchain -> Check All Blocks
   -> Return Block Index, Confirmations, Metadata

3. Batch Verification:
   Verifier -> List of Certificate Hashes
   -> Build Merkle Tree -> Generate Proofs
   -> Verify Each Against Blockchain + Merkle Root

4. Tamper Detection:
   Validator -> Validate Each Block
   -> Check Hash Links -> Check Hash Integrity
   -> Report Tampered Block Indices
```

### Security Model

| Threat | Mitigation |
|--------|------------|
| Certificate forgery | SHA-256 hash of all certificate fields |
| Transaction spoofing | RSA digital signatures on all TXs |
| Chain tampering | Linked hashes + proof-of-work |
| Replay attacks | Unique transaction hashes + timestamps |
| Batch fraud | Merkle tree inclusion proofs |

### Consensus Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `difficulty` | 4 | Leading zero bits for PoW |
| `target_block_time` | 10s | Target block interval |
| `adjustment_interval` | 10 blocks | Difficulty recalculation period |
| `mining_reward` | 10.0 | Reward per mined block |

### Future Improvements

1. **PBFT or PoS consensus**: Replace PoW with more efficient consensus
2. **IPFS storage**: Store actual certificates off-chain
3. **Smart contracts**: Programmable issuance rules
4. **REST API**: HTTP interface for integration
5. **Web UI**: Browser-based explorer dashboard
