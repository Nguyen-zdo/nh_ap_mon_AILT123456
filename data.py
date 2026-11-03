"""
Tải mạng đường bộ từ OpenStreetMap bằng OSMnx, làm sạch, kiểm tra, lưu để tái lập.

Cách chạy:
    python tai_du_lieu_osm.py              # dùng GeoJSON ranh giới Hoàn Kiếm cũ
    python tai_du_lieu_osm.py --force       # tải lại theo GeoJSON, bỏ qua cache

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
PLACE = "Hoàn Kiếm, Hà Nội, Việt Nam"   # ĐỔI THÀNH KHU VỰC CỦA BẠN
NETWORK_TYPE = "drive"                   # đề bài yêu cầu "drive"
DATA_DIR = Path("data")
RAW = DATA_DIR / "area_raw.graphml"
CLEAN = DATA_DIR / "area_clean.graphml"
META = DATA_DIR / "graph_meta.json"
PNG = DATA_DIR / "graph_overview.png"
BOUNDARY_FILE = Path("boundary") / "hoan_kiem_old.geojson"
# Máy chủ Overpass dự phòng khi máy chủ chính quá tải (danh sách có thể thay đổi theo thời gian)
OVERPASS_SERVERS = [
    "https://overpass-api.de/api",
    "https://z.overpass-api.de/api",
    "https://overpass.kumi.systems/api",
    "https://overpass.private.coffee/api",
]
ATTEMPTS_PER_SERVER = 3   # số lần thử mỗi máy chủ; chờ 5s, 10s, 20s (backoff nhân đôi)
# ------------------------------------------------------------------------------


def configure_osmnx():
    ox.settings.overpass_rate_limit = False   # không chờ kiểm tra /status (hay bị chặn/treo)
    ox.settings.requests_timeout = 180
    ox.settings.use_cache = True              # lưu cache truy vấn, lần sau không tải lại


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


def load_boundary_geojson(path=BOUNDARY_FILE):
    """Đọc ranh giới quận Hoàn Kiếm cũ từ GeoJSON cục bộ; không gọi Nominatim."""
    import geopandas as gpd
    from shapely.ops import unary_union

    if not Path(path).exists():
        raise FileNotFoundError(
            f"Không tìm thấy {path}. Hãy đặt GeoJSON ranh giới quận Hoàn Kiếm cũ "
            "(trước 01/07/2025) tại đúng đường dẫn này."
        )
    gdf = gpd.read_file(path)
    if gdf.empty:
        raise ValueError("GeoJSON ranh giới không có đối tượng hình học.")

    # Nếu file chứa nhiều quận, chỉ chọn feature có thuộc tính nhận diện Hoàn Kiếm.
    if len(gdf) > 1:
        mask = gdf.astype(str).apply(
            lambda row: row.str.contains(r"Hoàn\s*Kiếm|Hoan\s*Kiem", case=False, regex=True).any(),
            axis=1,
        )
        selected = gdf.loc[mask]
        if selected.empty:
            raise ValueError(
                "GeoJSON có nhiều feature nhưng không tìm thấy thuộc tính ghi Hoàn Kiếm. "
                "Không tự ý gộp toàn bộ các quận."
            )
        gdf = selected

    if gdf.crs is None:
        # GeoJSON chuẩn mặc định dùng WGS84; gán CRS theo đặc tả GeoJSON.
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")
    geom = unary_union([g for g in gdf.geometry if g is not None and not g.is_empty])
    if geom.geom_type not in ("Polygon", "MultiPolygon"):
        raise ValueError(f"Kiểu hình học không hợp lệ: {geom.geom_type}")

    # Kiểm tra diện tích trong hệ mét để tránh nhầm với ranh giới Hà Nội/toàn vùng khác.
    area_km2 = gpd.GeoSeries([geom], crs="EPSG:4326").to_crs("EPSG:32648").area.iloc[0] / 1_000_000
    if not 3.5 <= area_km2 <= 7.5:
        raise ValueError(
            f"Diện tích ranh giới là {area_km2:.2f} km², ngoài khoảng kiểm tra 3.5–7.5 km². "
            "Hãy xác minh đây đúng là quận Hoàn Kiếm cũ."
        )
    print(f"Đã đọc ranh giới cục bộ: {path} | diện tích {area_km2:.2f} km²")
    return geom, area_km2


def download(place=None, lat=None, lon=None, dist=2000):
    """Tải mạng đường drive bên trong ranh giới Hoàn Kiếm cũ từ GeoJSON cục bộ."""
    configure_osmnx()
    if lat is not None or lon is not None:
        raise ValueError("Chế độ A1 dùng toàn bộ ranh giới quận Hoàn Kiếm cũ, không dùng --lat/--lon/--dist.")

    polygon, area_km2 = load_boundary_geojson()
    print("Tải mạng đường theo đa giác ranh giới Hoàn Kiếm cũ ...")
    G = _download_with_fallback(
        ox.graph_from_polygon, polygon,
        network_type=NETWORK_TYPE,
        simplify=True,
        retain_all=True,
        truncate_by_edge=False,
    )
    return G, f"Hoàn Kiếm cũ (GeoJSON, {area_km2:.2f} km²)"


def largest_scc(G):
    """Thành phần liên thông mạnh lớn nhất (osmnx 1.x, 2.x, hoặc thuần NetworkX)."""
    try:
        return ox.truncate.largest_component(G, strongly=True)
    except (AttributeError, TypeError):
        try:
            return ox.utils_graph.get_largest_component(G, strongly=True)
        except (AttributeError, TypeError):
            scc = max(nx.strongly_connected_components(G), key=len)
            return G.subgraph(scc).copy()


def bo_sung_length(G):
    """Chỉ bổ sung length khi có cạnh thiếu. KHÔNG gọi add_edge_lengths vô điều kiện:
    hàm đó tính lại length bằng khoảng cách thẳng giữa hai nút và ghi đè chiều dài thực của OSM."""
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
        "--place", default=PLACE,
        help="Giữ tương thích lệnh cũ; chế độ A1 luôn dùng ranh giới GeoJSON Hoàn Kiếm cũ."
    )
    ap.add_argument("--lat", type=float, help=argparse.SUPPRESS)
    ap.add_argument("--lon", type=float, help=argparse.SUPPRESS)
    ap.add_argument("--dist", type=int, default=2000, help=argparse.SUPPRESS)
    ap.add_argument("--force", action="store_true", help="tải lại dù đã có file lưu")
    a = ap.parse_args()

    if (a.lat is None) != (a.lon is None):
        sys.exit("[LỖI] Cần đưa cả --lat và --lon.")
    DATA_DIR.mkdir(exist_ok=True)

    # Chỉ tái sử dụng cache nếu metadata xác nhận đó là dữ liệu Hoàn Kiếm cũ
    # tải từ GeoJSON. Cache Cửa Nam hoặc vùng khác sẽ tự động bị bỏ qua.
    da_co_file = RAW.exists() and CLEAN.exists() and META.exists()
    area_cache = ""
    if da_co_file:
        try:
            area_cache = json.loads(META.read_text(encoding="utf-8")).get("area", "")
        except (OSError, json.JSONDecodeError):
            area_cache = ""

    cache_dung_khu_vuc = area_cache.startswith("Hoàn Kiếm cũ (GeoJSON")
    if da_co_file and cache_dung_khu_vuc and not a.force:
        print("Đã có dữ liệu Hoàn Kiếm cũ hợp lệ, nạp lại từ GraphML.")
        G_raw, G_clean = ox.load_graphml(RAW), ox.load_graphml(CLEAN)
        area = area_cache
    else:
        if da_co_file and not cache_dung_khu_vuc:
            print(
                "[LƯU Ý] Cache hiện tại không phải dữ liệu toàn quận Hoàn Kiếm cũ "
                f"(metadata area={area_cache!r}). Sẽ tải lại theo GeoJSON."
            )
        elif a.force:
            print("Có --force: bỏ qua cache và tải dữ liệu mới.")
        G_raw, area = download(a.place, a.lat, a.lon, a.dist)
        G_raw = bo_sung_length(G_raw)
        G_clean = largest_scc(G_raw)
        ox.save_graphml(G_raw, RAW)
        ox.save_graphml(G_clean, CLEAN)

    st_raw = kiem_tra(G_raw, "Đồ thị gốc")
    st_clean = kiem_tra(G_clean, "Đồ thị đã làm sạch (thành phần liên thông mạnh lớn nhất)")
    bo_di = st_raw["nodes"] - st_clean["nodes"]
    print(f"\nĐã loại {bo_di} nút ({100 * bo_di / max(st_raw['nodes'], 1):.1f}%) không thuộc thành phần lớn nhất.")
    if st_raw["scc"] == 1:
        print("[LƯU Ý] Đồ thị gốc chỉ có 1 thành phần liên thông mạnh: chưa có sẵn ca 'không có đường'. "
              "Hãy mở rộng khu vực hoặc nêu rõ cách tạo ca đó trong báo cáo.")

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