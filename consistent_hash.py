import hashlib

class ConsistentHashRing:
    def __init__(self, nodes=None, replicas=3):
        self.replicas = replicas
        self.ring = {}
        self.sorted_keys = []
        if nodes:
            for node in nodes:
                self.add_node(node)

    def add_node(self, node):
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            self.ring[key] = node
            self.sorted_keys.append(key)
        self.sorted_keys.sort()

    def remove_node(self, node):
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            self.ring.pop(key, None)
            if key in self.sorted_keys:
                self.sorted_keys.remove(key)

    def get_node(self, key):
        if not self.ring:
            return None
        hash_key = self._hash(key)
        for k in self.sorted_keys:
            if hash_key <= k:
                return self.ring[k]
        return self.ring[self.sorted_keys[0]]

    def get_replica_nodes(self, key):
        nodes = []
        sorted_keys = self.sorted_keys
        if not sorted_keys:
            return nodes
        hash_key = self._hash(key)
        for k in sorted_keys:
            if hash_key <= k:
                node = self.ring[k]
                if node not in nodes:
                    nodes.append(node)
                break
        idx = sorted_keys.index(k) if k in sorted_keys else 0
        while len(nodes) < min(self.replicas, len(self.ring) // self.replicas):
            next_idx = (idx + 1) % len(sorted_keys)
            next_node = self.ring[sorted_keys[next_idx]]
            if next_node not in nodes:
                nodes.append(next_node)
            idx = next_idx
        return nodes

    def _hash(self, key):
        return int(hashlib.sha256(key.encode()).hexdigest(), 16)