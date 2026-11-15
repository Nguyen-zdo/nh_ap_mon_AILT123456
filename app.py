"""Demo Streamlit: chọn hai điểm trên bản đồ, so sánh Dijkstra và A*."""
import json
from pathlib import Path
import osmnx as ox
import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point

from algorithms import dijkstra, astar
from experiments import find_graph

# ──────────────────────────────────────────────
# CẤU HÌNH TRANG
# ──────────────────────────────────────────────
@st.cache_resource
def load_meta():
    meta_path = Path("data") / "graph_meta.json"
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"area": "Hoàn Kiếm & Ba Đình"}

meta_data = load_meta()
area_name = meta_data.get("area", "Hoàn Kiếm & Ba Đình")
area_display = area_name.split("(")[0].strip() if "(" in area_name else area_name

st.set_page_config(
    page_title=f"Tìm đường giao hàng – {area_display}",
    layout="wide",
    page_icon="🗺️",
)

# CSS tùy chỉnh giao diện
st.markdown("""
<style>
/* ── Chống mờ / fade khi rerun & load lại ── */
[data-stale="true"],
[data-stale="true"] * {
    opacity: 1 !important;
    filter: none !important;
    transition: none !important;
}
.element-container:has([data-stale="true"]) {
    opacity: 1 !important;
    filter: none !important;
}
div[data-testid="stStatusWidget"] {
    visibility: hidden !important;
}

/* Thanh tiêu đề */
.main-title { font-size: 2rem; font-weight: 700; color: #ffffff; margin-bottom: 0; }
.sub-title   { font-size: 0.95rem; color: #6c757d; margin-top: 2px; }

/* ── Iframe bản đồ: full width, nền trắng, bỏ viền tối ── */
iframe {
    filter: none !important;
    opacity: 1 !important;
    width: 100% !important;
    display: block !important;
    border-radius: 10px !important;
    border: none !important;
}
/* Xóa nền tối bao quanh iframe */
div[data-testid="stIframe"],
div.element-container:has(iframe),
div.stIframe {
    background: white !important;
    border-radius: 10px !important;
    padding: 0 !important;
    overflow: hidden !important;
    width: 100% !important;
}
div[data-testid="stIframe"]:hover,
div.element-container:has(iframe):hover {
    filter: none !important;
    opacity: 1 !important;
}
/* Xóa pseudo-element overlay */
div[data-testid="stIframe"]::after,
div.element-container:has(iframe)::after {
    display: none !important;
}

/* Card kết quả */
.result-card {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 16px 20px;
    border-left: 5px solid;
    margin-bottom: 10px;
    color: #1a1a2e !important;
}
.card-dijkstra { border-color: #0055FF; }
.card-astar    { border-color: #FF6600; }
.card-title    { font-size: 1.0rem; font-weight: 600; margin-bottom: 4px; color: #1a1a2e !important; }
.card-dist     { font-size: 1.8rem; font-weight: 700; color: #1a1a2e !important; }
.card-meta     { font-size: 0.82rem; color: #6c757d !important; margin-top: 4px; }
.card-dist small { font-size: 1rem; color: #555 !important; }

/* Hộp trạng thái điểm S/T */
.point-box {
    display: inline-block;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 0.88rem;
    font-weight: 600;
    margin: 4px 6px 4px 0;
}
.point-s { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.point-t { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
.point-empty { background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }

/* Nút hành động */
div[data-testid="column"] button {
    width: 100%;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 0;
}

/* Thanh tiến trình bước */
.step-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 10px 0 16px 0;
    font-size: 0.88rem;
}
.step-badge {
    background: #0055FF;
    color: white;
    border-radius: 50%;
    width: 24px; height: 24px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.75rem;
    flex-shrink: 0;
}
.step-done { background: #28a745; }
.step-line { flex: 1; height: 2px; background: #dee2e6; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# TIÊU ĐỀ
# ──────────────────────────────────────────────
st.markdown(f'<div class="main-title">🗺️ Tìm tuyến giao hàng ngắn nhất</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">Khu vực: <b>{area_display}</b> &nbsp;|&nbsp; Thuật toán: Dijkstra & A* &nbsp;|&nbsp; Dữ liệu: OpenStreetMap</div>', unsafe_allow_html=True)
st.markdown("---")

# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
TILES_MAP = {
    "🗺️ OpenStreetMap": {
        "tiles": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attr": "&copy; OpenStreetMap contributors"
    },
    "🗺️ OSM Pháp (nhanh)": {
        "tiles": "https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png",
        "attr": "&copy; OpenStreetMap contributors"
    },
    "🛰️ Google Maps": {
        "tiles": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        "attr": "Google Maps"
    },
}

with st.sidebar:
    st.markdown("## ⚙️ Cài đặt bản đồ")
    tile_choice = st.selectbox("Nền bản đồ:", list(TILES_MAP.keys()), index=0)
    current_tile = TILES_MAP[tile_choice]["tiles"]
    current_attr = TILES_MAP[tile_choice]["attr"]

    st.markdown("---")
    st.markdown("**Lớp hiển thị:**")
    show_boundary = st.checkbox(f"🔴 Ranh giới {area_display}", value=True)
    show_network  = st.checkbox("🔘 Mạng lưới đường bộ", value=False,
                                help="Hiển thị khung xương đồ thị các cạnh nối giữa các nút giao")
    show_both_routes = st.checkbox("🔵🟠 Hiển thị cả 2 tuyến Dijkstra & A*", value=False,
                                   help="Vẽ đồng thời tuyến Dijkstra (xanh) và A* (cam) lên bản đồ kết quả")

    st.markdown("---")
    # Thông tin đồ thị
    n_meta = meta_data.get("clean", {})
    st.markdown("**📊 Thông tin đồ thị:**")
    st.markdown(f"- Số nút: **{n_meta.get('nodes', '?')}**")
    st.markdown(f"- Số cạnh: **{n_meta.get('edges', '?')}**")
    st.markdown(f"- Đường 1 chiều: **{n_meta.get('oneway_edges', '?')}** cạnh")
    st.markdown(f"- Ngày tải: `{meta_data.get('download_date', '?')}`")

# ──────────────────────────────────────────────
# TẢI DỮ LIỆU
# ──────────────────────────────────────────────
@st.cache_resource
def load_graph():
    return ox.load_graphml(find_graph())

@st.cache_resource
def load_boundary():
    candidates = [
        Path("boundary") / "hoan_kiem_ba_dinh.geojson",
        Path("boundary") / "ba_dinh.geojson",
        Path("boundary") / "hoan_kiem_old.geojson",
    ]
    if "Ba Đình" in area_name and "Hoàn Kiếm" in area_name:
        candidates = [Path("boundary") / "hoan_kiem_ba_dinh.geojson"] + candidates
    elif "Ba Đình" in area_name:
        candidates = [Path("boundary") / "ba_dinh.geojson"] + candidates
    elif "Hoàn Kiếm" in area_name:
        candidates = [Path("boundary") / "hoan_kiem_old.geojson"] + candidates
    for boundary_path in candidates:
        if boundary_path.exists():
            gdf = gpd.read_file(boundary_path)
            from shapely.geometry import Polygon, MultiPolygon
            g = gdf.geometry.iloc[0]
            if g.geom_type == "Polygon" and len(g.interiors) > 0:
                fixed_g = Polygon(g.exterior.coords)
                gdf["geometry"] = [fixed_g]
                g = fixed_g
            elif g.geom_type == "MultiPolygon":
                fixed_g = MultiPolygon([Polygon(p.exterior.coords) for p in g.geoms])
                gdf["geometry"] = [fixed_g]
                g = fixed_g
            return gdf, g
    return None, None

G = load_graph()
gdf_boundary, poly_boundary = load_boundary()

@st.cache_data
def get_network_lines():
    return [
        [(float(G.nodes[u]["y"]), float(G.nodes[u]["x"])),
         (float(G.nodes[v]["y"]), float(G.nodes[v]["x"]))]
        for u, v in G.edges()
    ]

nodes = list(G.nodes)
xs = [float(G.nodes[n]["x"]) for n in nodes]
ys = [float(G.nodes[n]["y"]) for n in nodes]
center = [sum(ys)/len(ys), sum(xs)/len(xs)]
bounds = [[min(ys), min(xs)], [max(ys), max(xs)]]

# ──────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────
for key in ("S", "T"):
    if key not in st.session_state:
        st.session_state[key] = None

# ──────────────────────────────────────────────
# THANH TRẠNG THÁI ĐIỂM S / T + HƯỚNG DẪN
# ──────────────────────────────────────────────
def _fmt_coord(pt):
    if pt:
        return f"{pt[0]:.4f}, {pt[1]:.4f}"
    return None

s_set = st.session_state.S is not None
t_set = st.session_state.T is not None

# Chỉ dẫn theo bước
step1_done = s_set
step2_done = t_set
col_s, col_sep, col_t, col_reset = st.columns([3, 0.3, 3, 1.5])

with col_s:
    if s_set:
        st.markdown(f'<div class="point-box point-s">🟢 Điểm S: {_fmt_coord(st.session_state.S)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="point-box point-empty">🟡 Điểm S: Chưa chọn</div>', unsafe_allow_html=True)
with col_sep:
    st.markdown("<div style='text-align:center;font-size:1.5rem;color:#ccc;padding-top:4px'>→</div>", unsafe_allow_html=True)
with col_t:
    if t_set:
        st.markdown(f'<div class="point-box point-t">🔴 Điểm T: {_fmt_coord(st.session_state.T)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="point-box point-empty">🟡 Điểm T: Chưa chọn</div>', unsafe_allow_html=True)
with col_reset:
    if st.button("🗑️ Xóa S & T", use_container_width=True):
        st.session_state.S = st.session_state.T = None
        st.rerun()

# Hướng dẫn từng bước
if not s_set:
    st.info("**Bước 1:** Nhấn vào bản đồ bên dưới để chọn vị trí, sau đó bấm **\"Đặt làm S\"**.")
elif not t_set:
    st.info("**Bước 2:** Nhấn vào vị trí đích trên bản đồ, sau đó bấm **\"Đặt làm T\"**.")
else:
    st.success("✅ Đã chọn cả S và T — đang tính toán tuyến đường bên dưới.")

# ──────────────────────────────────────────────
# HÀM VẼ BẢN ĐỒ
# ──────────────────────────────────────────────
def create_base_map():
    m = folium.Map(location=center, zoom_start=14, tiles=current_tile, attr=current_attr)
    m.fit_bounds(bounds)

    # 1. Ranh giới
    if show_boundary and gdf_boundary is not None:
        folium.GeoJson(
            gdf_boundary,
            name=f"Ranh giới {area_display}",
            style_function=lambda x: {
                "color": "#D32F2F", "weight": 3, "dashArray": "6, 4",
                "fillColor": "#FF5252", "fillOpacity": 0.07,
            },
            tooltip=f"Địa phận {area_display}"
        ).add_to(m)

    # 2. Mạng lưới đường bộ (gộp thành 1 đối tượng duy nhất để tối ưu hiệu năng)
    if show_network:
        folium.PolyLine(
            get_network_lines(),
            color="#999999", weight=1, opacity=0.35
        ).add_to(m)

    # 3. Marker S – nhãn chữ rõ ràng
    if st.session_state.S:
        folium.Marker(
            st.session_state.S,
            tooltip=f"<b>S – Điểm xuất phát</b><br>{_fmt_coord(st.session_state.S)}",
            icon=folium.DivIcon(
                html="""<div style="
                    background:#28a745;color:white;font-weight:700;font-size:13px;
                    border-radius:50%;width:30px;height:30px;line-height:30px;
                    text-align:center;border:2px solid white;
                    box-shadow:0 2px 6px rgba(0,0,0,0.4);">S</div>""",
                icon_size=(30, 30), icon_anchor=(15, 15)
            )
        ).add_to(m)

    # 4. Marker T – nhãn chữ rõ ràng
    if st.session_state.T:
        folium.Marker(
            st.session_state.T,
            tooltip=f"<b>T – Điểm đích</b><br>{_fmt_coord(st.session_state.T)}",
            icon=folium.DivIcon(
                html="""<div style="
                    background:#dc3545;color:white;font-weight:700;font-size:13px;
                    border-radius:50%;width:30px;height:30px;line-height:30px;
                    text-align:center;border:2px solid white;
                    box-shadow:0 2px 6px rgba(0,0,0,0.4);">T</div>""",
                icon_size=(30, 30), icon_anchor=(15, 15)
            )
        ).add_to(m)

    return m

# ──────────────────────────────────────────────
# BẢN ĐỒ CHÍNH (chọn điểm)
# ──────────────────────────────────────────────
base_map = create_base_map()
clicked = st_folium(base_map, height=500, width=None, returned_objects=["last_clicked"])

# Kiểm tra điểm nhấn có trong ranh giới
is_inside = True
lat_click = lng_click = None
if clicked and clicked.get("last_clicked"):
    lat_click = clicked["last_clicked"]["lat"]
    lng_click = clicked["last_clicked"]["lng"]
    if poly_boundary is not None:
        p = Point(lng_click, lat_click)
        is_inside = poly_boundary.contains(p)
        if not is_inside:
            st.warning(f"⚠️ Điểm nhấn ({lat_click:.4f}, {lng_click:.4f}) nằm **ngoài** ranh giới {area_display}. Vui lòng chọn điểm bên trong đường viền đỏ.")

# Nút đặt S / T
c1, c2, c3 = st.columns([2, 2, 3])
with c1:
    if st.button("📍 Đặt làm S (xuất phát)", use_container_width=True):
        if lat_click is None:
            st.warning("Hãy nhấn vào bản đồ trước.")
        elif not is_inside:
            st.error(f"Điểm nằm ngoài {area_display}.")
        else:
            st.session_state.S = [lat_click, lng_click]
            st.rerun()
with c2:
    if st.button("🏁 Đặt làm T (đích đến)", use_container_width=True):
        if lat_click is None:
            st.warning("Hãy nhấn vào bản đồ trước.")
        elif not is_inside:
            st.error(f"Điểm nằm ngoài {area_display}.")
        else:
            st.session_state.T = [lat_click, lng_click]
            st.rerun()
with c3:
    if lat_click:
        st.markdown(f"<small style='color:#6c757d'>📌 Vừa nhấn: `{lat_click:.5f}, {lng_click:.5f}` {'✅ Trong vùng' if is_inside else '❌ Ngoài vùng'}</small>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# KẾT QUẢ TÌM ĐƯỜNG
# ──────────────────────────────────────────────
if s_set and t_set:
    st.markdown("---")
    st.markdown("### 📊 Kết quả tìm đường")

    s_node = ox.distance.nearest_nodes(G, X=st.session_state.S[1], Y=st.session_state.S[0])
    t_node = ox.distance.nearest_nodes(G, X=st.session_state.T[1], Y=st.session_state.T[0])

    if s_node == t_node:
        st.warning("⚠️ Hai điểm được ánh xạ vào cùng một nút giao — hãy chọn 2 điểm cách xa hơn.")
    else:
        with st.spinner("Đang tính toán tuyến đường..."):
            rd = dijkstra(G, s_node, t_node)
            ra = astar(G, s_node, t_node)

        if not rd["found"]:
            st.error("❌ Không tìm được tuyến đường có hướng từ S đến T (do quy tắc đường một chiều).")
        else:
            # ── Thẻ kết quả song song
            col_d, col_a = st.columns(2)

            saved_pct = (1 - ra["expanded"] / max(rd["expanded"], 1)) * 100
            same_dist = abs(rd["distance_m"] - ra["distance_m"]) < 0.01

            with col_d:
                st.markdown(f"""
                <div class="result-card card-dijkstra">
                    <div class="card-title">🔵 Dijkstra</div>
                    <div class="card-dist">{rd['distance_m']:.1f} <small>m</small></div>
                    <div class="card-meta">
                        ⏱ {rd['time_s']*1000:.3f} ms &nbsp;|&nbsp;
                        🔍 {rd['expanded']} nút mở rộng
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_a:
                st.markdown(f"""
                <div class="result-card card-astar">
                    <div class="card-title">🟠 A* (Haversine)</div>
                    <div class="card-dist">{ra['distance_m']:.1f} <small>m</small></div>
                    <div class="card-meta">
                        ⏱ {ra['time_s']*1000:.3f} ms &nbsp;|&nbsp;
                        🔍 {ra['expanded']} nút mở rộng
                        {"&nbsp;|&nbsp; <b>tiết kiệm " + f"{saved_pct:.0f}%" + " nút</b>" if saved_pct > 0 else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Nhận xét tóm tắt
            if same_dist:
                st.success(f"✅ Hai thuật toán cho **cùng kết quả** ({rd['distance_m']:.1f} m). A* tiết kiệm **{saved_pct:.0f}%** số nút cần duyệt.")
            else:
                st.info(f"ℹ️ Kết quả chiều dài khác nhau — kiểm tra lại thuật toán.")

            # ── Nút giao gần nhất (chi tiết kỹ thuật — thu gọn)
            with st.expander("🔧 Chi tiết kỹ thuật (nút giao)", expanded=False):
                sn = G.nodes[s_node]
                tn = G.nodes[t_node]
                st.markdown(f"""
                | | Nút ID | Vĩ độ | Kinh độ |
                |---|---|---|---|
                | 🟢 S (gần nhất) | `{s_node}` | {float(sn['y']):.5f} | {float(sn['x']):.5f} |
                | 🔴 T (gần nhất) | `{t_node}` | {float(tn['y']):.5f} | {float(tn['x']):.5f} |
                """)
                st.caption(f"Tuyến đi qua {len(rd['nodes'])} nút giao.")

            # ── Bản đồ tuyến đường
            st.markdown("#### 🗺️ Bản đồ tuyến đường")
            route_map = create_base_map()

            # Tọa độ Dijkstra
            d_net = [(float(G.nodes[n]["y"]), float(G.nodes[n]["x"])) for n in rd["nodes"]]
            d_full = [tuple(st.session_state.S)] + d_net + [tuple(st.session_state.T)]

            if show_both_routes:
                # Tuyến A*
                a_net = [(float(G.nodes[n]["y"]), float(G.nodes[n]["x"])) for n in ra["nodes"]]
                a_full = [tuple(st.session_state.S)] + a_net + [tuple(st.session_state.T)]

                folium.PolyLine(
                    d_full, color="#0055FF", weight=6, opacity=0.85,
                    tooltip=f"Dijkstra – {rd['distance_m']:.1f} m"
                ).add_to(route_map)
                folium.PolyLine(
                    a_full, color="#FF6600", weight=4, opacity=0.9,
                    dash_array="8, 4",
                    tooltip=f"A* – {ra['distance_m']:.1f} m"
                ).add_to(route_map)

                st.caption("🔵 Đường liền: Dijkstra &nbsp;|&nbsp; 🟠 Đường đứt nét: A*")
            else:
                folium.PolyLine(
                    d_full, color="#0055FF", weight=6, opacity=0.9,
                    tooltip=f"Tuyến ngắn nhất – {rd['distance_m']:.1f} m"
                ).add_to(route_map)

            st_folium(route_map, height=500, width=None, key="route_map")
            st.caption("© OpenStreetMap contributors (ODbL) | Dữ liệu đường bộ có hướng, trọng số theo chiều dài thực (mét).")
