from collections import defaultdict, deque


def _adjacency(edges):
    adj = defaultdict(list)
    for e in edges:
        adj[e["source"]].append(e)
    return adj


def find_paths_to_targets(graph, start_ids, target_ids, max_hops=8, max_paths_per_start=5):
    
    if not start_ids or not target_ids:
        return []

    adj = _adjacency(graph["edges"])
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    findings = []

    for start in start_ids:
        found = 0
        queue = deque([(start, [start], [])])

        while queue and found < max_paths_per_start:
            cur, path, edges = queue.popleft()

            if cur in target_ids and len(path) > 1:
                findings.append({
                    "start_id": start,
                    "start_name": nodes_by_id.get(start, {}).get("name", start),
                    "target_id": cur,
                    "target_name": nodes_by_id.get(cur, {}).get("name", cur),
                    "hops": len(edges),
                    "nodes": [nodes_by_id.get(x, {"id": x, "name": x, "kind": "Unknown"})
                              for x in path],
                    "edges": list(edges),
                })
                found += 1
                continue

            if len(edges) >= max_hops:
                continue

            for e in adj.get(cur, []):
                
                if e["target"] in path:
                    continue
                queue.append((e["target"], path + [e["target"]], edges + [e]))
    return findings
