"""
Các thuật toán tìm đường ngắn nhất tối ưu: Dijkstra và A*.
Đã được tối ưu hóa:
1. Heuristic Haversine tiền tính góc lượng giác và Memoization Cache.
2. Duyệt kề trực tiếp qua NetworkX Adjacency Mapping (loại bỏ chi phí hàm get lặp).
3. Min-Heap Tie-breaking ưu tiên mục tiêu để hội tụ nhanh.
4. Tương thích 100% định dạng Node ID (int/str) và hỗ trợ trọng số tắc đường (traffic_weights).
"""
import heapq
import math
import time


def haversine_distance(lat1, lon1, lat2, lon2):
    """Tính khoảng cách chim bay theo mét giữa hai tọa độ địa lý (Haversine formula)."""
    R = 6371000.0  # bán kính Trái Đất (mét)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi * 0.5)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda * 0.5)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def _get_edge_length(G, u, v, traffic_weights=None):
    """Lấy chiều dài hoặc trọng số có tính đến tắc đường giữa 2 nút u và v."""
    if traffic_weights and (u, v) in traffic_weights:
        return traffic_weights[(u, v)]

    edge_dict = G[u][v]
    if hasattr(G, "is_multigraph") and G.is_multigraph():
        base_len = min(float(d.get("length", 1.0)) for d in edge_dict.values())
    else:
        base_len = float(edge_dict.get("length", 1.0))

    return base_len


def _match_node(G, node):
    """Tự động chuyển đổi giữa int và str để tương thích 100% với kiểu nút của đồ thị G."""
    if node in G:
        return node
    if isinstance(node, str) and node.isdigit() and int(node) in G:
        return int(node)
    if str(node) in G:
        return str(node)
    return node


def dijkstra(G, source, target, traffic_weights=None):
    """
    Thuật toán Dijkstra tối ưu tìm đường đi ngắn nhất từ source đến target.
    Sử dụng Min-Heap (heapq) và truy xuất cạnh trực tiếp qua Adjacency Map.
    """
    source = _match_node(G, source)
    target = _match_node(G, target)
    t0 = time.perf_counter()

    if source not in G or target not in G:
        return {
            "found": False,
            "distance_m": float("inf"),
            "time_s": time.perf_counter() - t0,
            "expanded": 0,
            "nodes": [],
            "visited_nodes": [],
        }

    if source == target:
        return {
            "found": True,
            "distance_m": 0.0,
            "time_s": time.perf_counter() - t0,
            "expanded": 0,
            "nodes": [source],
            "visited_nodes": [source],
        }

    distances = {source: 0.0}
    predecessors = {}
    pq = [(0.0, source)]
    visited = set()
    visited_order = []
    expanded = 0

    # Tối ưu truy xuất cạnh trực tiếp qua adjacency dict
    adj = G._adj if hasattr(G, "_adj") else G.adj
    is_multi = hasattr(G, "is_multigraph") and G.is_multigraph()

    while pq:
        dist_u, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        visited_order.append(u)
        expanded += 1

        if u == target:
            break

        u_neighbors = adj[u]
        if traffic_weights:
            for v, edge_dict in u_neighbors.items():
                w = traffic_weights.get((u, v))
                if w is None:
                    if is_multi:
                        w = min(float(d.get("length", 1.0)) for d in edge_dict.values())
                    else:
                        w = float(edge_dict.get("length", 1.0))
                new_dist = dist_u + w
                if new_dist < distances.get(v, float("inf")):
                    distances[v] = new_dist
                    predecessors[v] = u
                    heapq.heappush(pq, (new_dist, v))
        else:
            for v, edge_dict in u_neighbors.items():
                if is_multi:
                    w = min(float(d.get("length", 1.0)) for d in edge_dict.values())
                else:
                    w = float(edge_dict.get("length", 1.0))
                new_dist = dist_u + w
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
            "visited_nodes": visited_order,
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
        "visited_nodes": visited_order,
    }


def astar(G, source, target, traffic_weights=None):
    """
    Thuật toán A* tối ưu tìm đường đi ngắn nhất từ source đến target.
    Các cải tiến:
    - Tiền tính toán tọa độ đích và hàm lượng giác cố định.
    - Memoization cache cho hàm Heuristic Haversine tránh lặp lại phép tính sin/cos/atan2.
    - Min-Heap Tie-breaking ưu tiên nút gần đích hơn.
    - Truy xuất cạnh trực tiếp qua Adjacency dict.
    """
    source = _match_node(G, source)
    target = _match_node(G, target)
    t0 = time.perf_counter()

    if source not in G or target not in G:
        return {
            "found": False,
            "distance_m": float("inf"),
            "time_s": time.perf_counter() - t0,
            "expanded": 0,
            "nodes": [],
            "visited_nodes": [],
        }

    if source == target:
        return {
            "found": True,
            "distance_m": 0.0,
            "time_s": time.perf_counter() - t0,
            "expanded": 0,
            "nodes": [source],
            "visited_nodes": [source],
        }

    R = 6371000.0
    nodes_data = G.nodes
    target_node = nodes_data[target]
    target_lat = float(target_node["y"])
    target_lon = float(target_node["x"])
    target_phi = math.radians(target_lat)
    target_lambda = math.radians(target_lon)
    cos_target_phi = math.cos(target_phi)

    h_cache = {}

    def get_h(node):
        cached = h_cache.get(node)
        if cached is not None:
            return cached
        nd = nodes_data[node]
        phi1 = math.radians(float(nd["y"]))
        dphi = target_phi - phi1
        dlambda = target_lambda - math.radians(float(nd["x"]))
        a = math.sin(dphi * 0.5)**2 + math.cos(phi1) * cos_target_phi * math.sin(dlambda * 0.5)**2
        h_val = R * (2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a)))
        h_cache[node] = h_val
        return h_val

    h_s = get_h(source)
    g_score = {source: 0.0}
    predecessors = {}
    pq = [(h_s, h_s, 0.0, source)]
    visited = set()
    visited_order = []
    expanded = 0

    adj = G._adj if hasattr(G, "_adj") else G.adj
    is_multi = hasattr(G, "is_multigraph") and G.is_multigraph()

    while pq:
        f_u, h_u, dist_u, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        visited_order.append(u)
        expanded += 1

        if u == target:
            break

        u_neighbors = adj[u]
        if traffic_weights:
            for v, edge_dict in u_neighbors.items():
                w = traffic_weights.get((u, v))
                if w is None:
                    if is_multi:
                        w = min(float(d.get("length", 1.0)) for d in edge_dict.values())
                    else:
                        w = float(edge_dict.get("length", 1.0))
                tentative_g = dist_u + w
                if tentative_g < g_score.get(v, float("inf")):
                    g_score[v] = tentative_g
                    h_v = get_h(v)
                    f_val = tentative_g + h_v
                    predecessors[v] = u
                    heapq.heappush(pq, (f_val, h_v, tentative_g, v))
        else:
            for v, edge_dict in u_neighbors.items():
                if is_multi:
                    w = min(float(d.get("length", 1.0)) for d in edge_dict.values())
                else:
                    w = float(edge_dict.get("length", 1.0))
                tentative_g = dist_u + w
                if tentative_g < g_score.get(v, float("inf")):
                    g_score[v] = tentative_g
                    h_v = get_h(v)
                    f_val = tentative_g + h_v
                    predecessors[v] = u
                    heapq.heappush(pq, (f_val, h_v, tentative_g, v))

    t1 = time.perf_counter()
    if target not in predecessors and source != target:
        return {
            "found": False,
            "distance_m": float("inf"),
            "time_s": t1 - t0,
            "expanded": expanded,
            "nodes": [],
            "visited_nodes": visited_order,
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
        "visited_nodes": visited_order,
    }
