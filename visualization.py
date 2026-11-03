"""Vẽ mạng đường và một số tuyến tìm được để dán vào báo cáo."""
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import osmnx as ox

ROOT = Path(__file__).resolve().parent

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

def save_network_image(G, output=None):
    """Xuất ảnh tổng quan mạng lưới đường bộ."""
    output = Path(output or ROOT / "results" / "network.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = ox.plot_graph(
        G, node_size=0, edge_color="#777777", edge_linewidth=0.55,
        bgcolor="white", show=False, close=False
    )
    fig.text(0.01, 0.01, "© OpenStreetMap contributors", fontsize=8)
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output

def save_route_image(G, route_nodes, output, title="Tuyến đường"):
    """Xuất ảnh tuyến đường tìm được bởi thuật toán Dijkstra / A*."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = ox.plot_graph_route(
        G, route_nodes, route_color="#e53935", route_linewidth=3,
        node_size=0, edge_color="#aaaaaa", edge_linewidth=0.5,
        bgcolor="white", show=False, close=False
    )
    ax.set_title(title, fontsize=11, fontweight="bold")
    fig.text(0.01, 0.01, "© OpenStreetMap contributors", fontsize=8)
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output

if __name__ == "__main__":
    g_path = latest_graph()
    print(f"Đang nạp đồ thị từ: {g_path}")
    G = ox.load_graphml(g_path)
    img_path = save_network_image(G)
    print(f"Đã lưu ảnh tổng quan mạng lưới tại: {img_path}")
