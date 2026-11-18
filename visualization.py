import json
import sys
from pathlib import Path

# Đảm bảo in tiếng Việt chuẩn trên Console Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

# Import các thuật toán từ algorithms.py
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from algorithms import dijkstra, astar

# Kiểm tra thư viện OSMnx
try:
    import osmnx as ox
    HAS_OSMNX = True
except ImportError:
    HAS_OSMNX = False


def latest_graph():
    """Tìm file đồ thị hợp lệ trong thư mục data/."""
    candidates = [
        ROOT / "data" / "area_clean.graphml",
        ROOT / "data" / "area_raw.graphml",
    ] + list((ROOT / "data").glob("**/area_clean.graphml"))

    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("Chưa có dữ liệu đồ thị. Hãy chạy python data.py trước.")


def load_graph_safe(g_path):
    """Nạp đồ thị bằng OSMnx nếu có, hoặc dùng NetworkX làm dự phòng."""
    if HAS_OSMNX:
        try:
            return ox.load_graphml(g_path)
        except Exception:
            pass
    return nx.read_graphml(g_path)


def save_network_image(G, output=None):
    """Xuất ảnh tổng quan mạng lưới đường bộ."""
    output = Path(output or ROOT / "results" / "network.png")
    output.parent.mkdir(parents=True, exist_ok=True)

    meta_path = ROOT / "data" / "graph_meta.json"
    area_name = "Hoàn Kiếm & Ba Đình"
    if meta_path.exists():
        try:
            meta_json = json.loads(meta_path.read_text(encoding="utf-8"))
            area_name = meta_json.get("area", area_name)
            if "(" in area_name:
                area_name = area_name.split("(")[0].strip()
        except Exception:
            pass

    fig, ax = plt.subplots(figsize=(10, 10), facecolor="white")

    # Vẽ toàn bộ các cạnh đường bộ
    for u, v in G.edges():
        ux, uy = float(G.nodes[u]["x"]), float(G.nodes[u]["y"])
        vx, vy = float(G.nodes[v]["x"]), float(G.nodes[v]["y"])
        ax.plot([ux, vx], [uy, vy], color="#666666", linewidth=0.6, alpha=0.75, zorder=1)

    ax.set_title(f"Mạng lưới đường bộ {area_name} (Drive)", fontsize=13, fontweight="bold", pad=12)
    ax.set_aspect("equal", "datalim")
    ax.axis("off")
    fig.text(0.02, 0.02, "© OpenStreetMap contributors (ODbL)", fontsize=8, color="#555555")

    try:
        fig.savefig(output, dpi=220, bbox_inches="tight")
        print(f"[OK] Đã lưu ảnh tổng quan mạng lưới tại: {output}")
    except OSError as e:
        print(f"[Lưu ý] Không thể ghi file {output}: {e}")
    finally:
        plt.close(fig)

    return output


def save_route_image(G, route_nodes, output, title="Tuyến đường", desc=""):
    """Xuất ảnh tuyến đường tìm được bởi thuật toán Dijkstra / A*."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 10), facecolor="white")

    # 1. Vẽ mạng đường nền (màu xám nhạt)
    for u, v in G.edges():
        ux, uy = float(G.nodes[u]["x"]), float(G.nodes[u]["y"])
        vx, vy = float(G.nodes[v]["x"]), float(G.nodes[v]["y"])
        ax.plot([ux, vx], [uy, vy], color="#b0bec5", linewidth=0.5, alpha=0.65, zorder=1)

    # 2. Vẽ tuyến đường tìm được (màu đỏ đậm nổi bật)
    if route_nodes and len(route_nodes) > 1:
        rx = [float(G.nodes[n]["x"]) for n in route_nodes]
        ry = [float(G.nodes[n]["y"]) for n in route_nodes]
        ax.plot(rx, ry, color="#d32f2f", linewidth=3.5, alpha=0.9, zorder=3, label="Lộ trình tối ưu")

        # Đánh dấu điểm bắt đầu S (Xanh lá) và điểm đích T (Đỏ)
        ax.scatter([rx[0]], [ry[0]], color="#2e7d32", s=90, edgecolors="white", linewidth=1.5, zorder=5, label="Xuất phát (S)")
        ax.scatter([rx[-1]], [ry[-1]], color="#c2185b", s=90, edgecolors="white", linewidth=1.5, zorder=5, label="Đích đến (T)")

        ax.legend(loc="upper right", fontsize=9, framealpha=0.9)

    full_title = title
    if desc:
        full_title += f"\n({desc})"
    ax.set_title(full_title, fontsize=11, fontweight="bold", pad=10)
    ax.set_aspect("equal", "datalim")
    ax.axis("off")
    fig.text(0.02, 0.02, "© OpenStreetMap contributors (ODbL)", fontsize=8, color="#555555")

    try:
        fig.savefig(output, dpi=220, bbox_inches="tight")
        print(f"[OK] Đã lưu ảnh tuyến tại: {output}")
    except OSError as e:
        print(f"[Lưu ý] Không thể ghi file {output}: {e}")
    finally:
        plt.close(fig)

    return output


def export_sample_routes(G):
    """Xuất 3 tuyến mẫu phục vụ dán vào báo cáo theo yêu cầu đề bài."""
    results_dir = ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    sample_routes = [
        {
            "id": 1,
            "filename": "route_1_short.png",
            "s": "6539666887",
            "t": "10164900175",
            "name": "Tuyến 1 (Cự ly gần - Ba Đình): Hoàng thành Thăng Long -> Cột Cờ Hà Nội",
        },
        {
            "id": 2,
            "filename": "route_2_long.png",
            "s": "309815539",
            "t": "11465167153",
            "name": "Tuyến 2 (Liên quận Ba Đình - Hoàn Kiếm): Lăng Bác -> Hồ Hoàn Kiếm",
        },
        {
            "id": 3,
            "filename": "route_3_detour.png",
            "s": "9581996745",
            "t": "6646847595",
            "name": "Tuyến 3 (Trục dài xuyên suốt 2 quận): Lotte Liễu Giai -> Tràng Tiền Plaza",
        },
    ]

    print("\n" + "=" * 75)
    print("XUẤT ẢNH 3 TUYẾN TIÊU BIỂU CHO BÁO CÁO")
    print("=" * 75)

    for item in sample_routes:
        s, t = item["s"], item["t"]
        res = astar(G, s, t)
        if res["found"]:
            dist_m = res["distance_m"]
            nodes_count = len(res["nodes"])
            desc_text = f"Chiều dài: {dist_m:.1f}m | Số nút: {nodes_count}"
            out_file = results_dir / item["filename"]
            save_route_image(G, res["nodes"], out_file, title=item["name"], desc=desc_text)
        else:
            print(f"[!] Không tìm thấy tuyến giữa {s} và {t}")


if __name__ == "__main__":
    g_path = latest_graph()
    print(f"[*] Đang nạp đồ thị từ: {g_path}")
    G = load_graph_safe(g_path)
    print(f"[*] Đồ thị nạp thành công: {G.number_of_nodes()} nút, {G.number_of_edges()} cạnh.\n")

    # 1. Xuất ảnh tổng quan mạng lưới
    save_network_image(G)

    # 2. Xuất 3 ảnh tuyến mẫu cho báo cáo
    export_sample_routes(G)

    print("\n[HOÀN TẤT] Bạn có thể kiểm tra các ảnh vừa tạo trong thư mục results/ để chèn vào báo cáo.")
