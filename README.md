# Dynamo Key-Value Store

A scaled-down implementation of Amazon's Dynamo key-value store for IIT Ropar's Advanced Operating Systems course. Features consistent hashing, hinted handoff, gossip protocol, and a web UI.

## Features
- **Consistent Hashing**: Distributes keys across nodes (5000, 5001, 5002).
- **Hinted Handoff**: Stores data for down nodes, syncing on recovery.
- **Gossip Protocol**: Updates node statuses every 2 seconds.
- **UI**: Displays nodes (green/red) and keys at `http://localhost:5000/ui`.
