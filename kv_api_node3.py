from flask import Flask, request, jsonify, render_template
import requests
from consistent_hash import ConsistentHashRing
import logging
import time
import random
import threading
import json

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
store = {}  # Main key-value store
hints = {}  # {key: {value, timestamp, target_node}}
node_states = {
    "localhost:5000": {"status": "alive", "timestamp": time.time()},
    "localhost:5001": {"status": "alive", "timestamp": time.time()},
    "localhost:5002": {"status": "alive", "timestamp": time.time()}
}
nodes = ["localhost:5000", "localhost:5001", "localhost:5002"]
current_node = "localhost:5002"
ring = ConsistentHashRing(nodes=nodes, replicas=3)
GOSSIP_INTERVAL = 2

def gossip():
    while True:
        time.sleep(GOSSIP_INTERVAL)
        other_nodes = [n for n in nodes if n != current_node]
        if other_nodes:
            target = random.choice(other_nodes)
            try:
                logging.debug(f"Gossiping to {target}")
                response = requests.post(
                    f"http://{target}/gossip",
                    json={"states": node_states},
                    timeout=3
                )
                if response.status_code == 200:
                    node_states[target]["status"] = "alive"
                    node_states[target]["timestamp"] = time.time()
            except requests.RequestException as e:
                logging.error(f"Gossip to {target} failed: {e}")
                node_states[target]["status"] = "down"
                node_states[target]["timestamp"] = time.time()

@app.route('/')
def hello():
    return "Hello, Flask is running!"

@app.route('/ui')
def ui():
    return render_template('dashboard.html', nodes=node_states, data=store)

@app.route('/ui/nodes')
def ui_nodes():
    return jsonify(node_states)

@app.route('/ui/data')
def ui_data():
    return jsonify(store)

@app.route('/kv', methods=['POST'])
def create_update():
    data = request.json
    key = data.get('key')
    value = data.get('value')
    if key is None or value is None:
        return jsonify({"error": "Key and value are required"}), 400
    target_nodes = ring.get_replica_nodes(key)
    logging.debug(f"POST key={key}, target_nodes={target_nodes}, node_states={node_states}")
    store[key] = value
    for node in target_nodes:
        if node != current_node:
            if node_states.get(node, {}).get("status") == "alive":
                try:
                    logging.debug(f"Forwarding POST to {node}")
                    requests.post(f"http://{node}/kv", json={"key": key, "value": value}, timeout=10)
                except requests.RequestException as e:
                    logging.error(f"Failed to forward POST to {node}: {e}")
                    hints[key] = {"value": value, "timestamp": time.time(), "target_node": node}
            else:
                logging.debug(f"Storing hint for {node} (down)")
                hints[key] = {"value": value, "timestamp": time.time(), "target_node": node}
    return jsonify({"status": "success", "key": key, "value": value})

@app.route('/kv/<key>', methods=['GET'])
def read(key):
    value = store.get(key)
    if value is None:
        return jsonify({"error": "Key not found"}), 404
    return jsonify({"key": key, "value": value})

@app.route('/kv/<key>', methods=['DELETE'])
def delete(key):
    target_nodes = ring.get_replica_nodes(key)
    logging.debug(f"DELETE key={key}, target_nodes={target_nodes}, node_states={node_states}")
    if key in store:
        del store[key]
    for node in target_nodes:
        if node != current_node:
            if node_states.get(node, {}).get("status") == "alive":
                try:
                    logging.debug(f"Forwarding DELETE to {node}")
                    requests.delete(f"http://{node}/kv/{key}", timeout=10)
                except requests.RequestException as e:
                    logging.error(f"Failed to forward DELETE to {node}: {e}")
                    hints[key] = {"value": None, "timestamp": time.time(), "target_node": node}
            else:
                logging.debug(f"Storing hint for {node} (down)")
                hints[key] = {"value": None, "timestamp": time.time(), "target_node": node}
    return jsonify({"status": "success", "key": key})

@app.route('/kv', methods=['PUT'])
def update():
    data = request.json
    key = data.get('key')
    value = data.get('value')
    if key is None or value is None:
        return jsonify({"error": "Key and value are required"}), 400
    target_nodes = ring.get_replica_nodes(key)
    logging.debug(f"PUT key={key}, target_nodes={target_nodes}, node_states={node_states}")
    if key not in store:
        return jsonify({"error": "Key not found"}), 404
    store[key] = value
    for node in target_nodes:
        if node != current_node:
            if node_states.get(node, {}).get("status") == "alive":
                try:
                    logging.debug(f"Forwarding PUT to {node}")
                    requests.put(f"http://{node}/kv", json={"key": key, "value": value}, timeout=10)
                except requests.RequestException as e:
                    logging.error(f"Failed to forward PUT to {node}: {e}")
                    hints[key] = {"value": value, "timestamp": time.time(), "target_node": node}
            else:
                logging.debug(f"Storing hint for {node} (down)")
                hints[key] = {"value": value, "timestamp": time.time(), "target_node": node}
    return jsonify({"status": "success", "key": key, "value": value})

@app.route('/sync_hints', methods=['POST'])
def sync_hints():
    logging.debug(f"Syncing hints: {hints}")
    for key, hint in list(hints.items()):
        node = hint["target_node"]
        value = hint["value"]
        if node_states.get(node, {}).get("status") == "alive":
            try:
                if value is None:
                    logging.debug(f"Syncing DELETE for key={key} to {node}")
                    requests.delete(f"http://{node}/kv/{key}", timeout=10)
                else:
                    logging.debug(f"Syncing POST key={key}, value={value} to {node}")
                    requests.post(f"http://{node}/kv", json={"key": key, "value": value}, timeout=10)
                del hints[key]
            except requests.RequestException as e:
                logging.error(f"Failed to sync hint for key={key} to {node}: {e}")
        else:
            logging.debug(f"Skipping sync to {node} (down)")
    return jsonify({"status": "sync complete"})

@app.route('/gossip', methods=['POST'])
def receive_gossip():
    data = request.json
    remote_states = data.get("states", {})
    for node, info in remote_states.items():
        if node != current_node:
            local_info = node_states.get(node, {"status": "down", "timestamp": 0})
            if info["timestamp"] > local_info["timestamp"]:
                node_states[node] = info
    logging.debug(f"Updated states: {node_states}")
    return jsonify({"status": "gossip received"})

if __name__ == '__main__':
    import sys
    port = 5000 if len(sys.argv) < 2 else int(sys.argv[1])
    threading.Thread(target=gossip, daemon=True).start()
    app.run(host='0.0.0.0', port=port)