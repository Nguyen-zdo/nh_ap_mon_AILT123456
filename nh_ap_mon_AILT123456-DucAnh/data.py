"""
Tải mạng đường bộ từ OpenStreetMap bằng OSMnx, làm sạch, kiểm tra, lưu để tái lập.

Cách chạy:
    python data.py                             # tải mạng đường mở rộng Hoàn Kiếm & Ba Đình
    python data.py --district both             # gộp cả 2 quận: Hoàn Kiếm & Ba Đình (~14.5 km²)
    python data.py --district ba_dinh          # chỉ riêng quận Ba Đình (~9.3 km²)
    python data.py --district hoan_kiem        # chỉ riêng quận Hoàn Kiếm cũ (~5.2 km²)
    python data.py --force                     # tải lại và ghi đè dữ liệu cũ

Đầu ra (thư mục data/): area_raw.graphml, area_clean.graphml, graph_meta.json, graph_overview.png
Dữ liệu: © OpenStreetMap contributors, giấy phép ODbL.
"""
import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

if sys.platform == "win32":  # tránh UnicodeEncodeError trên console Windows
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox

# ----------------------------- CẤU HÌNH MẶC ĐỊNH -----------------------------
PLACE = "Hoàn Kiếm & Ba Đình, Hà Nội, Việt Nam"
NETWORK_TYPE = "all"                            # chuyển sang "all" để phục vụ bài toán giao hàng bằng xe máy
DATA_DIR = Path("data")
RAW = DATA_DIR / "area_raw.graphml"
CLEAN = DATA_DIR / "area_clean.graphml"
META = DATA_DIR / "graph_meta.json"
PNG = DATA_DIR / "graph_overview.png"

BOUNDARY_DIR = Path("boundary")
DISTRICTS_JSON = BOUNDARY_DIR / "__districts_hanoi_00.1.0.json"
DEFAULT_BOUNDARY = BOUNDARY_DIR / "hoan_kiem_ba_dinh.geojson"

# Máy chủ Overpass dự phòng khi máy chủ chính quá tải
OVERPASS_SERVERS = [
    "https://overpass-api.de/api",
    "https://z.overpass-api.de/api",
    "https://overpass.kumi.systems/api",
    "https://overpass.private.coffee/api",
]
ATTEMPTS_PER_SERVER = 3   # số lần thử mỗi máy chủ; chờ 5s, 10s, 20s (backoff nhân đôi)
# ------------------------------------------------------------------------------


def configure_osmnx():
    ox.settings.overpass_rate_limit = False   # không chờ kiểm tra /status (tránh bị dừng chờ 60s)
    ox.settings.doh_url_template = None       # dùng DNS hệ thống, tránh phân giải IP bị nghẽn
    ox.settings.requests_timeout = 180
    ox.settings.use_cache = True              # lưu cache truy vấn, lần sau không tải lại
    ox.settings.http_user_agent = "OSMnx Python package (https://github.com/gboeing/osmnx)"


def _download_with_fallback(func, *args, **kwargs):
    """Gọi hàm tải đồ thị; lỗi thì chờ (backoff) rồi thử lại, hết lượt thì chuyển máy chủ khác."""
    last_err = None
    for server in OVERPASS_SERVERS:
        ox.settings.overpass_url = server
        wait = 5
        for attempt in range(1, ATTEMPTS_PER_SERVER + 1):
            try:
                print(f"  -> Máy chủ {server} (lần {attempt}/{ATTEMPTS_PER_SERVER}) ...")
                G = func(*args, **kwargs)
                print(f"  -> Thành công với {server}")
                return G
            except Exception as e:
                last_err = e
                print(f"     [Cảnh báo] {type(e).__name__}: {str(e)[:150]}")
                if attempt < ATTEMPTS_PER_SERVER:
                    print(f"     Chờ {wait}s rồi thử lại ...")
                    time.sleep(wait)
                    wait *= 2
    raise RuntimeError(f"Mọi máy chủ Overpass đều không phản hồi. Lỗi cuối: {last_err}")


def get_or_create_boundary(district="both"):
    """
    Tạo hoặc đọc file GeoJSON ranh giới phù hợp:
    - 'both': Hoàn Kiếm & Ba Đình (gộp 2 quận)
    - 'ba_dinh': Quận Ba Đình
    - 'hoan_kiem': Quận Hoàn Kiếm cũ
    """
    import geopandas as gpd
    from shapely.ops import unary_union

    BOUNDARY_DIR.mkdir(parents=True, exist_ok=True)

    if district == "both":
        geo_path = BOUNDARY_DIR / "hoan_kiem_ba_dinh.geojson"
        target_names = ["HoànKiếm", "BaĐình"]
        label = "Hoàn Kiếm & Ba Đình"
    elif district in ("ba_dinh", "badinh"):
        geo_path = BOUNDARY_DIR / "ba_dinh.geojson"
        target_names = ["BaĐình"]
        label = "Ba Đình"
    else:
        geo_path = BOUNDARY_DIR / "hoan_kiem_old.geojson"
        target_names = ["HoànKiếm"]
        label = "Hoàn Kiếm cũ"

    from shapely.geometry import Polygon, MultiPolygon
    from shapely.ops import unary_union

    def _fill_holes(g):
        if g.geom_type == "Polygon":
            return Polygon(g.exterior.coords)
        elif g.geom_type == "MultiPolygon":
            return MultiPolygon([Polygon(p.exterior.coords) for p in g.geoms])
        return g

    if geo_path.exists():
        gdf = gpd.read_file(geo_path)
        geom = unary_union([g for g in gdf.geometry if g is not None and not g.is_empty])
        geom = _fill_holes(geom)
    else:
        if not DISTRICTS_JSON.exists():
            raise FileNotFoundError(f"Không tìm thấy {DISTRICTS_JSON} để trích xuất ranh giới.")
        districts_gdf = gpd.read_file(DISTRICTS_JSON)
        matched = districts_gdf[districts_gdf["NAME_2"].isin(target_names)]
        if matched.empty:
            raise ValueError(f"Không tìm thấy quận {target_names} trong {DISTRICTS_JSON}")
        geom = unary_union(matched.geometry)
        geom = _fill_holes(geom)
        gdf_out = gpd.GeoDataFrame([{"name": label, "geometry": geom}], crs=districts_gdf.crs)
        gdf_out.to_file(geo_path, driver="GeoJSON")
        print(f"Đã trích xuất và lưu ranh giới mới (đã loại bỏ khe hở tam giác): {geo_path}")

    # Tính diện tích (km2)
    area_km2 = gpd.GeoSeries([geom], crs="EPSG:4326").to_crs("EPSG:32648").area.iloc[0] / 1_000_000
    if not (3.0 <= area_km2 <= 25.0):
        raise ValueError(f"Diện tích {area_km2:.2f} km² bất thường đối với khu vực {label}.")

    print(f"Ranh giới sử dụng: {geo_path.name} | Khu vực: {label} ({area_km2:.2f} km²)")
    return geom, label, area_km2, geo_path


def download(district="both"):
    """Tải mạng đường drive theo ranh giới polygon GeoJSON."""
    configure_osmnx()
    polygon, label, area_km2, _ = get_or_create_boundary(district)
    print(f"Đang tải mạng đường theo đa giác ranh giới {label} ...")
    G = _download_with_fallback(
        ox.graph_from_polygon, polygon,
        network_type=NETWORK_TYPE,
        simplify=True,
        retain_all=True,
        truncate_by_edge=False,
    )
    return G, f"{label} (GeoJSON, {area_km2:.2f} km²)"


def ket_noi_ranh_gioi(G):
    """Bổ sung các đoạn đường liên quận bị cắt bởi ranh giới hành chính."""
    from algorithms import haversine_distance

    # 1. Đoạn phố Nguyễn Thái Học nối Ba Đình - Hoàn Kiếm qua rìa Đống Đa
    u, v = 318244325, 322505287
    if u in G.nodes and v in G.nodes and not G.has_edge(u, v):
        dist = haversine_distance(float(G.nodes[u]['y']), float(G.nodes[u]['x']), float(G.nodes[v]['y']), float(G.nodes[v]['x']))
        G.add_edge(u, v, key=0, name='Phố Nguyễn Thái Học', length=dist, oneway=True, highway='primary')
        print(f"[Đã nối ranh giới] Đã bổ sung cạnh nối {u} -> {v} (Phố Nguyễn Thái Học, {dist:.1f}m) giữa Ba Đình và Hoàn Kiếm.")

    # 2. Đoạn phố Láng Hạ nối cụm Thành Công - Láng Hạ (nam Ba Đình) vào mạng lưới chính
    u2, v2 = 724833172, 308728680
    if u2 in G.nodes and v2 in G.nodes and not G.has_edge(u2, v2):
        dist2 = haversine_distance(float(G.nodes[u2]['y']), float(G.nodes[u2]['x']), float(G.nodes[v2]['y']), float(G.nodes[v2]['x']))
        G.add_edge(u2, v2, key=0, name='Phố Láng Hạ', length=dist2, oneway=True, highway='primary')
        print(f"[Đã nối ranh giới] Đã bổ sung cạnh nối {u2} -> {v2} (Phố Láng Hạ, {dist2:.1f}m) kết nối cụm Thành Công - Láng Hạ.")

    return G


# Bộ lọc loại bỏ đường không phù hợp cho phương tiện giao thông (xe máy / shipper)
NON_MOTO_HIGHWAYS = {
    'steps', 'footway', 'pedestrian', 'corridor', 'path',
    'cycleway', 'track', 'bridleway', 'elevator', 'escalator'
}
RESTRICTED_ACCESS = {'private', 'no', 'permit'}

def _to_set(val):
    if isinstance(val, list):
        return set(str(x) for x in val)
    return {str(val)} if val else set()

def loc_duong_xe_may(G):
    """
    Loại bỏ các loại đường không dành cho phương tiện giao hàng (xe máy):
    - Bậc thang bộ (steps), thang máy, thang cuốn
    - Đường dành riêng cho người đi bộ (footway, pedestrian, corridor, path)
    - Đường nội bộ cấm hoặc yêu cầu giấy phép (access=private, no, permit)
    - Tuyến cấm xe cơ giới / xe máy (motor_vehicle=no, motorcycle=no)
    """
    to_remove = []
    for u, v, k, d in G.edges(keys=True, data=True):
        hw_set = _to_set(d.get('highway'))
        access_set = _to_set(d.get('access'))
        motor_vehicle_set = _to_set(d.get('motor_vehicle'))
        motorcycle_set = _to_set(d.get('motorcycle'))

        if hw_set & NON_MOTO_HIGHWAYS:
            to_remove.append((u, v, k))
        elif (access_set & RESTRICTED_ACCESS) and ('yes' not in motorcycle_set):
            to_remove.append((u, v, k))
        elif ('no' in motor_vehicle_set) or ('no' in motorcycle_set):
            to_remove.append((u, v, k))

    for u, v, k in to_remove:
        if G.has_edge(u, v, key=k):
            G.remove_edge(u, v, key=k)

    print(f"[Lọc xe máy] Đã loại bỏ {len(to_remove)} cạnh không phù hợp (đường đi bộ, bậc thang, đường cấm/nội bộ).")
    return G


def largest_scc(G):
    """Thành phần liên thông mạnh lớn nhất (osmnx 1.x, 2.x, hoặc thuần NetworkX)."""
    G = ket_noi_ranh_gioi(G)
    G = loc_duong_xe_may(G)
    try:
        return ox.truncate.largest_component(G, strongly=True)
    except (AttributeError, TypeError):
        try:
            return ox.utils_graph.get_largest_component(G, strongly=True)
        except (AttributeError, TypeError):
            scc = max(nx.strongly_connected_components(G), key=len)
            return G.subgraph(scc).copy()


def bo_sung_length(G):
    """Chỉ bổ sung length khi có cạnh thiếu. KHÔNG ghi đè chiều dài thực của OSM."""
    if any("length" not in d for _, _, d in G.edges(data=True)):
        print("[Lưu ý] Có cạnh thiếu length, bổ sung bằng khoảng cách giữa hai đầu nút.")
        G = ox.distance.add_edge_lengths(G)
    return G


def kiem_tra(G, ten):
    """In thống kê và kiểm tra các điều kiện Dijkstra/A* cần."""
    assert G.is_directed(), "Đồ thị phải có hướng"
    n, m = G.number_of_nodes(), G.number_of_edges()
    lengths = [d.get("length") for _, _, d in G.edges(data=True)]
    thieu = sum(1 for x in lengths if x is None)
    am = sum(1 for x in lengths if x is not None and x < 0)
    nhieu_canh = sum(1 for u, v in set(G.edges()) if G.number_of_edges(u, v) > 1)
    mot_chieu = sum(1 for _, _, d in G.edges(data=True) if d.get("oneway") in (True, "True", "true"))
    thieu_toa_do = sum(1 for _, d in G.nodes(data=True) if "x" not in d or "y" not in d)
    n_scc = nx.number_strongly_connected_components(G)
    print(f"\n--- {ten} ---")
    print(f"Số nút: {n} | Số cạnh: {m} | Thành phần liên thông mạnh: {n_scc}")
    if lengths and thieu < len(lengths):
        ok = [x for x in lengths if x is not None]
        print(f"Chiều dài cạnh (m): min {min(ok):.1f}, trung bình {sum(ok)/len(ok):.1f}, max {max(ok):.1f}")
    print(f"Cạnh thiếu length: {thieu} | cạnh length âm: {am} | cặp nút có cạnh song song: {nhieu_canh}")
    print(f"Cạnh đánh dấu một chiều: {mot_chieu} | nút thiếu tọa độ: {thieu_toa_do}")
    assert thieu == 0 and am == 0, "Có cạnh thiếu hoặc âm length: Dijkstra/A* sẽ sai"
    assert thieu_toa_do == 0, "Có nút thiếu tọa độ: không tính được heuristic"
    return {"nodes": n, "edges": m, "scc": n_scc, "oneway_edges": mot_chieu}


def ve_anh(G, duong_dan):
    fig, ax = ox.plot_graph(G, node_size=0, edge_linewidth=0.5, show=False, close=False)
    fig.text(0.01, 0.01, "© OpenStreetMap contributors", fontsize=7)
    fig.savefig(duong_dan, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Đã lưu ảnh: {duong_dan}")


def main():
    ap = argparse.ArgumentParser(description="Tải mạng đường OSM bằng OSMnx")
    ap.add_argument(
        "--district", default="both", choices=["both", "ba_dinh", "hoan_kiem"],
        help="Khu vực tải: 'both' (Hoàn Kiếm & Ba Đình), 'ba_dinh', hoặc 'hoan_kiem'"
    )
    ap.add_argument("--place", default=PLACE, help="Tên hiển thị địa danh")
    ap.add_argument("--force", action="store_true", help="tải lại dù đã có file lưu")
    a = ap.parse_args()

    DATA_DIR.mkdir(exist_ok=True)

    target_prefix = {
        "both": "Hoàn Kiếm & Ba Đình",
        "ba_dinh": "Ba Đình",
        "hoan_kiem": "Hoàn Kiếm cũ"
    }.get(a.district, "Hoàn Kiếm")

    da_co_file = RAW.exists() and CLEAN.exists() and META.exists()
    area_cache = ""
    if da_co_file:
        try:
            area_cache = json.loads(META.read_text(encoding="utf-8")).get("area", "")
        except (OSError, json.JSONDecodeError):
            area_cache = ""

    cache_dung_khu_vuc = area_cache.startswith(target_prefix)
    if da_co_file and cache_dung_khu_vuc and not a.force:
        print(f"Đã có dữ liệu {target_prefix} hợp lệ trong cache, nạp lại từ GraphML.")
        G_raw = ox.load_graphml(RAW)
        G_raw = bo_sung_length(G_raw)
        G_clean = largest_scc(G_raw)
        ox.save_graphml(G_clean, CLEAN)
        area = area_cache
    else:
        if da_co_file and not cache_dung_khu_vuc:
            print(
                f"[LƯU Ý] Cache hiện tại ({area_cache!r}) khác khu vực yêu cầu ({target_prefix}). "
                "Sẽ tải dữ liệu mới."
            )
        elif a.force:
            print("Có --force: bỏ qua cache và tải dữ liệu mới.")

        G_raw, area = download(district=a.district)
        G_raw = bo_sung_length(G_raw)
        G_clean = largest_scc(G_raw)
        ox.save_graphml(G_raw, RAW)
        ox.save_graphml(G_clean, CLEAN)

    st_raw = kiem_tra(G_raw, "Đồ thị gốc")
    st_clean = kiem_tra(G_clean, "Đồ thị đã làm sạch (thành phần liên thông mạnh lớn nhất)")
    bo_di = st_raw["nodes"] - st_clean["nodes"]
    print(f"\nĐã loại {bo_di} nút ({100 * bo_di / max(st_raw['nodes'], 1):.1f}%) không thuộc thành phần lớn nhất.")
    if st_raw["scc"] == 1:
        print("[LƯU Ý] Đồ thị gốc chỉ có 1 thành phần liên thông mạnh.")

    ngay_tai = date.today().isoformat()
    if META.exists() and not (a.force or not da_co_file):
        ngay_tai = json.loads(META.read_text(encoding="utf-8")).get("download_date", ngay_tai)
    meta = {
        "area": area, "network_type": NETWORK_TYPE, "download_date": ngay_tai,
        "raw": st_raw, "clean": st_clean, "osmnx_version": ox.__version__,
        "attribution": "© OpenStreetMap contributors (ODbL)",
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã lưu: {RAW}, {CLEAN}, {META}")

    ve_anh(G_clean, PNG)

    xs = [d["x"] for _, d in G_clean.nodes(data=True)]
    ys = [d["y"] for _, d in G_clean.nodes(data=True)]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    try:  # lưu ý: X = kinh độ, Y = vĩ độ
        nut = ox.distance.nearest_nodes(G_clean, X=cx, Y=cy)
        print(f"Ví dụ: tâm khu vực (lat={cy:.5f}, lon={cx:.5f}) gần nhất với nút {nut}")
    except Exception as e:
        print(f"Không thể tìm nút gần nhất: {e}")


if __name__ == "__main__":
    main()
