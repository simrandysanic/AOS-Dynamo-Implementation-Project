# Distributed System Test Log

## Failure Handling Test
- **Setup**: Stopped node 2 (localhost:5001).
- **POST test:123 (5000)**: Success, {"key":"test","status":"success","value":"123"}
- **GET test (5000)**: Success, {"key":"test","value":"123"}
- **GET test (5002)**: Success, {"key":"test","value":"123"}
- **PUT test:456 (5000)**: Success, {"key":"test","status":"success","value":"456"}
- **DELETE test (5000)**: Success, {"key":"test","status":"success"}
- **Notes**: All operations succeeded despite node 2 failure, confirming fault tolerance.

## Hinted Handoff Test
- **Setup**: Stopped node 2 (localhost:5001).
- **POST hint:789 (5000)**: Success, {"key":"hint","status":"success","value":"789"}
- **Sync Hints (5000)**: Success, {"status":"sync complete"}
- **Restarted node 2 (5001)**.
- **GET hint (5001)**: Success, {"key":"hint","value":"789"}
- **Notes**: Handoff worked; timeouts to 5002 and 5000 in node 2 logs didn’t impact success.

## Gossip Protocol Test
- **Setup**: Stopped node 2 (localhost:5001).
- **Gossip Check (5000, after 10s)**: Log confirmed 5001 marked "down".
- **Restarted node 2 (5001)**.
- **Gossip Check (5000, after 10s)**: Log confirmed 5001 marked "alive".
- **POST gossip:123 (5000)**: Success, {"key":"gossip","status":"success","value":"123"}
- **Sync Hints (5000)**: Success, {"status":"sync complete"}
- **GET gossip (5001)**: Success, {"key":"gossip","value":"123"}
- **Notes**: Gossip protocol accurately updated node statuses; no issues.