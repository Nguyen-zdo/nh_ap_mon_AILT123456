"""Các thuật toán tìm đường ngắn nhất: Dijkstra và A*."""
import heapq
import math
import time

def haversine_distance(lat1, lon1, lat2, lon2):
    """Tính khoảng cách chim bay theo mét giữa hai tọa độ địa lý (Haversine formula)."""
    R = 6371000.0  # bán kính Trái Đất (mét)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def _get_edge_length(G, u, v):
    """Lấy chiều dài nhỏ nhất (mét) giữa 2 nút u và v trên MultiDiGraph."""
    edge_dict = G[u][v]
    if hasattr(edge_dict, "values"):
        return min(float(d.get("length", 1.0)) for d in edge_dict.values())
    return float(edge_dict.get("length", 1.0))

def dijkstra(G, source, target):
    """Thuật toán Dijkstra tìm đường đi ngắn nhất từ source đến target."""
    t0 = time.perf_counter()
    if source == target:
        return {
            "found": True,
            "distance_m": 0.0,
            "time_s": time.perf_counter() - t0,
            "expanded": 0,
            "nodes": [source],
        }

    distances = {source: 0.0}
    predecessors = {}
    pq = [(0.0, source)]
    visited = set()
    expanded = 0

    while pq:
        dist_u, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        expanded += 1

        if u == target:
            break

        for v in G.neighbors(u):
            weight = _get_edge_length(G, u, v)
            new_dist = dist_u + weight
            if new_dist < distances.get(v, float("inf")):
                distances[v] = new_dist
                predecessors[v] = u
                heapq.heappush(pq, (new_dist, v))

    t1 = time.perf_counter()
    if target not in predecessors and source != target:
        return {
            "found": False,
            "distance_m": float("inf"),
            "time_s": t1 - t0,
            "expanded": expanded,
            "nodes": [],
        }

    # Tái tạo tuyến đường
    curr = target
    path = []
    while curr is not None:
        path.append(curr)
        curr = predecessors.get(curr)
    path.reverse()

    return {
        "found": True,
        "distance_m": distances[target],
        "time_s": t1 - t0,
        "expanded": expanded,
        "nodes": path,
    }

def astar(G, source, target):
    """Thuật toán A* tìm đường đi ngắn nhất từ source đến target với heuristic Haversine."""
    t0 = time.perf_counter()
    if source == target:
        return {
            "found": True,
            "distance_m": 0.0,
            "time_s": time.perf_counter() - t0,
            "expanded": 0,
            "nodes": [source],
        }

    target_lat = float(G.nodes[target]["y"])
    target_lon = float(G.nodes[target]["x"])

    def h(node):
        lat = float(G.nodes[node]["y"])
        lon = float(G.nodes[node]["x"])
        return haversine_distance(lat, lon, target_lat, target_lon)

    g_score = {source: 0.0}
    f_score = {source: h(source)}
    predecessors = {}
    pq = [(f_score[source], 0.0, source)]
    visited = set()
    expanded = 0

    while pq:
        _, dist_u, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        expanded += 1

        if u == target:
            break

        for v in G.neighbors(u):
            weight = _get_edge_length(G, u, v)
            tentative_g = dist_u + weight
            if tentative_g < g_score.get(v, float("inf")):
                g_score[v] = tentative_g
                f_val = tentative_g + h(v)
                f_score[v] = f_val
                predecessors[v] = u
                heapq.heappush(pq, (f_val, tentative_g, v))

    t1 = time.perf_counter()
    if target not in predecessors and source != target:
        return {
            "found": False,
            "distance_m": float("inf"),
            "time_s": t1 - t0,
            "expanded": expanded,
            "nodes": [],
        }

    # Tái tạo tuyến đường
    curr = target
    path = []
    while curr is not None:
        path.append(curr)
        curr = predecessors.get(curr)
    path.reverse()

    return {
        "found": True,
        "distance_m": g_score[target],
        "time_s": t1 - t0,
        "expanded": expanded,
        "nodes": path,
    }
