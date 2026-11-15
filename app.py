"""Demo Streamlit: Tìm đường giao hàng ngắn nhất bằng Dijkstra & A* (Google Maps Style)."""
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
# CẤU HÌNH TRANG THEO CHUẨN GOOGLE MAPS
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
    page_title=f"Google Maps AI – {area_display}",
    layout="wide",
    page_icon="📍",
)

# CSS giao diện Google Material Design hiện đại, sáng sủa
st.markdown("""
<style>
/* ── Reset font & nền theo chuẩn Google Material ── */
html, body, [class*="css"] {
    font-family: 'Google Sans', Roboto, -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── Chống mờ khi Streamlit rerun ── */
[data-stale="true"], [data-stale="true"] * {
    opacity: 1 !important; filter: none !important; transition: none !important;
}
.element-container:has([data-stale="true"]) {
    opacity: 1 !important; filter: none !important;
}
div[data-testid="stStatusWidget"] { visibility: hidden !important; }



/* ── Khung tìm kiếm địa chỉ Google Search Card ── */
.search-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 4px rgba(60,64,67,0.12), 0 2px 6px rgba(60,64,67,0.08);
    border: 1px solid #dadce0;
    margin-bottom: 14px;
}
.search-title {
    font-size: 0.92rem; font-weight: 600; color: #202124; margin-bottom: 12px;
    display: flex; align-items: center; gap: 8px;
}

/* ── Thẻ thống kê kết quả Google Cards ── */
.stat-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(60,64,67,0.15);
    border-top: 4px solid;
    margin-bottom: 12px;
    border-left: 1px solid #e8eaed;
    border-right: 1px solid #e8eaed;
    border-bottom: 1px solid #e8eaed;
}
.stat-dijkstra { border-top-color: #1a73e8; }
.stat-astar    { border-top-color: #f29900; }
.stat-title {
    font-size: 0.92rem; font-weight: 600; color: #5f6368; text-transform: uppercase; letter-spacing: 0.5px;
}
.stat-dist {
    font-size: 2.1rem; font-weight: 700; color: #202124; margin: 6px 0;
}
.stat-meta {
    font-size: 0.85rem; color: #5f6368;
}

/* ── Hộp điểm S/T ── */
.pin-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 12px; border-radius: 20px; font-weight: 600; font-size: 0.85rem;
}
.pin-s { background: #e6f4ea; color: #137333; border: 1px solid #ceead6; }
.pin-t { background: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }

/* ── Bản đồ full width, bo tròn chuẩn Google ── */
iframe {
    width: 100% !important; border-radius: 12px !important;
    border: 1px solid #dadce0 !important;
    box-shadow: 0 1px 4px rgba(60,64,67,0.12) !important;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# DANH SÁCH ĐỊA DANH / ĐƯỜNG PHỐ TÌM KIẾM
# ──────────────────────────────────────────────
LANDMARKS = {
    "-- Nhấn vào bản đồ để chọn tọa độ tùy ý --": None,
    "🏛️ Hồ Hoàn Kiếm (Đền Ngọc Sơn)": (21.0306, 105.8524),
    "🛍️ Chợ Đồng Xuân": (21.0375, 105.8499),
    "🎭 Nhà hát Lớn Hà Nội": (21.0245, 105.8576),
    "🏬 Tràng Tiền Plaza": (21.0255, 105.8535),
    "⛪ Nhà thờ Lớn Hà Nội": (21.0288, 105.8494),
    "🏰 Hoàng thành Thăng Long": (21.0355, 105.8405),
    "🚩 Cột Cờ Hà Nội": (21.0325, 105.8398),
    "🏛️ Lăng Chủ tịch Hồ Chí Minh": (21.0368, 105.8346),
    "🏯 Chùa Trấn Quốc (Hồ Tây)": (21.0478, 105.8368),
    "🚉 Ga Hà Nội (Lê Duẩn)": (21.0245, 105.8415),
    "🌉 Đầu cầu Chương Dương": (21.0375, 105.8580),
    "🏥 Bệnh viện Hữu nghị Việt Đức": (21.0286, 105.8485),
    "🏥 Bệnh viện K (Quán Sứ)": (21.0258, 105.8475),
    "🏮 Ô Quan Chưởng": (21.0360, 105.8540),
    "🏮 Phố Hàng Gai": (21.0318, 105.8505),
    "🏮 Phố Hàng Bông": (21.0298, 105.8465),
    "🏮 Phố Tràng Tiền": (21.0252, 105.8550),
    "🌳 Công viên Bách Thảo": (21.0390, 105.8285),
    "🏛️ Văn Miếu Quốc Tử Giám": (21.0275, 105.8355),
    "🏬 TTTM Lotte Center (Liễu Giai)": (21.0325, 105.8125),
    "🏮 Phố Kim Mã": (21.0315, 105.8250),
}

# ──────────────────────────────────────────────
# SIDEBAR CÀI ĐẶT
# ──────────────────────────────────────────────
TILES_MAP = {
    "🗺️ Google Maps": {
        "tiles": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        "attr": "Google Maps"
    },
    "🗺️ OpenStreetMap": {
        "tiles": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attr": "&copy; OpenStreetMap contributors"
    },
    "🗺️ OSM Pháp (nhanh & sắc nét)": {
        "tiles": "https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png",
        "attr": "&copy; OpenStreetMap contributors"
    },
    "🛰️ Vệ tinh (Esri World Imagery)": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Esri, Maxar, Earthstar Geographics"
    },
}

with st.sidebar:
    st.markdown("### ⚙️ Tùy chọn bản đồ")
    tile_choice = st.selectbox("Kiểu bản đồ:", list(TILES_MAP.keys()), index=0)
    current_tile = TILES_MAP[tile_choice]["tiles"]
    current_attr = TILES_MAP[tile_choice]["attr"]

    st.markdown("---")
    st.markdown("### 🚦 Mô phỏng Giao thông & Tắc đường")
    traffic_mode = st.selectbox(
        "Tình trạng giao thông:",
        [
            "🟢 Thông thoáng (Bình thường)",
            "🔴 Giờ cao điểm (Tắc các trục chính)",
            "💥 Ùn tắc trên lộ trình (Test thuật toán né tắc)",
        ],
        index=0,
    )
    avoid_traffic = st.checkbox(
        "🛡️ Tự động tìm đường vòng né tắc",
        value=True,
        help="Khi phát hiện điểm tắc, thuật toán sẽ tự động tính toán lộ trình thay thế thông thoáng hơn."
    )

    st.markdown("---")
    st.markdown("**Lớp hiển thị phụ:**")
    show_boundary = st.checkbox(f"🔴 Ranh giới {area_display}", value=True)
    show_network  = st.checkbox("🔘 Khung xương mạng đường", value=False)
    show_both_routes = st.checkbox("🔵🟠 So sánh cả 2 tuyến Dijkstra & A*", value=False)

    st.markdown("---")
    n_meta = meta_data.get("clean", {})
    st.markdown(f"**📊 Dữ liệu mạng đường:**")
    st.markdown(f"- Quy mô: **{n_meta.get('nodes', '?')} nút**, **{n_meta.get('edges', '?')} cạnh**")
    st.markdown(f"- Đường 1 chiều: **{n_meta.get('oneway_edges', '?')} cạnh**")

# ──────────────────────────────────────────────
# TẢI DỮ LIỆU ĐỒ THỊ
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

def parse_geometry_coords(geom):
    """Lấy danh sách (lat, lon) từ Shapely LineString hoặc WKT."""
    if hasattr(geom, "coords"):
        return [(lat, lon) for lon, lat in geom.coords]
    if isinstance(geom, str) and geom.startswith("LINESTRING"):
        try:
            from shapely import wkt
            ls = wkt.loads(geom)
            return [(lat, lon) for lon, lat in ls.coords]
        except Exception:
            pass
    return None

def get_detailed_route_coords(G, route_nodes):
    """Trích xuất tọa độ chi tiết bám theo khúc cua thực tế (geometry) của các cạnh."""
    if not route_nodes:
        return []
    coords = []
    for i in range(len(route_nodes) - 1):
        u, v = route_nodes[i], route_nodes[i + 1]
        edge_data = G.get_edge_data(u, v)
        found_geom = False
        if edge_data:
            for d in edge_data.values():
                if "geometry" in d:
                    pts = parse_geometry_coords(d["geometry"])
                    if pts:
                        if coords:
                            coords.extend(pts[1:])
                        else:
                            coords.extend(pts)
                        found_geom = True
                        break
        if not found_geom:
            u_pt = (float(G.nodes[u]["y"]), float(G.nodes[u]["x"]))
            v_pt = (float(G.nodes[v]["y"]), float(G.nodes[v]["x"]))
            if not coords:
                coords.append(u_pt)
            coords.append(v_pt)
    return coords

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
# QUẢN LÝ ĐIỂM S VÀ T
# ──────────────────────────────────────────────
for key in ("S", "T", "S_name", "T_name"):
    if key not in st.session_state:
        st.session_state[key] = None

s_set = st.session_state.S is not None
t_set = st.session_state.T is not None
both_set = s_set and t_set

# ──────────────────────────────────────────────
# THANH TÌM KIẾM ĐỊA CHỈ GOOGLE MAPS
# ──────────────────────────────────────────────
with st.container():
    st.markdown('<div class="search-card">', unsafe_allow_html=True)
    st.markdown('<div class="search-title">🔍 Tìm kiếm địa điểm & Chọn lộ trình di chuyển</div>', unsafe_allow_html=True)

    col_search_s, col_search_t, col_actions = st.columns([2.5, 2.5, 1.5])

    landmark_names = list(LANDMARKS.keys())

    with col_search_s:
        choice_s = st.selectbox(
            "🟢 Điểm xuất phát (S):",
            landmark_names,
            index=0,
            help="Chọn địa danh có sẵn hoặc chọn mục đầu tiên để click trên bản đồ"
        )
        if choice_s != landmark_names[0]:
            st.session_state.S = list(LANDMARKS[choice_s])
            st.session_state.S_name = choice_s

    with col_search_t:
        choice_t = st.selectbox(
            "🔴 Điểm đến (T):",
            landmark_names,
            index=0,
            help="Chọn địa danh có sẵn hoặc chọn mục đầu tiên để click trên bản đồ"
        )
        if choice_t != landmark_names[0]:
            st.session_state.T = list(LANDMARKS[choice_t])
            st.session_state.T_name = choice_t

    with col_actions:
        st.write("") # căn lề
        st.write("")
        if st.button("🗑️ Đặt lại (Xóa S/T)", use_container_width=True):
            st.session_state.S = st.session_state.T = None
            st.session_state.S_name = st.session_state.T_name = None
            st.rerun()

    # Dòng tóm tắt trạng thái 2 điểm
    s_label = st.session_state.S_name or (f"{st.session_state.S[0]:.4f}, {st.session_state.S[1]:.4f}" if st.session_state.S else "Chưa chọn")
    t_label = st.session_state.T_name or (f"{st.session_state.T[0]:.4f}, {st.session_state.T[1]:.4f}" if st.session_state.T else "Chưa chọn")
    
    st.markdown(f"""
    <div style="margin-top: 6px;">
        <span class="pin-badge pin-s">🟢 Xuất phát: {s_label}</span>
        &nbsp; ➔ &nbsp;
        <span class="pin-badge pin-t">🔴 Đích đến: {t_label}</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# TÍNH TOÁN TUYẾN ĐƯỜNG (KHI ĐÃ CÓ CẢ S VÀ T)
# ──────────────────────────────────────────────
route_calculated = False
rd = ra = rd_base = None
congested_edges_list = []
is_rerouted = False
route_coords = []
route_bounds = None

if both_set:
    s_node = ox.distance.nearest_nodes(G, X=st.session_state.S[1], Y=st.session_state.S[0])
    t_node = ox.distance.nearest_nodes(G, X=st.session_state.T[1], Y=st.session_state.T[0])

    if s_node == t_node:
        st.warning("⚠️ Hai điểm được ánh xạ vào cùng một nút giao — hãy chọn 2 điểm cách xa nhau hơn.")
    else:
        # Lộ trình cơ bản
        rd_base = dijkstra(G, s_node, t_node)
        ra_base = astar(G, s_node, t_node)

        # Xử lý mô phỏng tắc đường
        traffic_weights = {}
        if traffic_mode != "🟢 Thông thoáng (Bình thường)":
            if traffic_mode == "💥 Ùn tắc trên lộ trình (Test thuật toán né tắc)" and rd_base["found"] and len(rd_base["nodes"]) >= 4:
                path_nodes = rd_base["nodes"]
                idx_start = max(1, len(path_nodes) // 3)
                for i in range(idx_start, min(idx_start + 2, len(path_nodes) - 1)):
                    congested_edges_list.append((path_nodes[i], path_nodes[i + 1]))
            elif traffic_mode == "🔴 Giờ cao điểm (Tắc các trục chính)":
                congest_keywords = ["Tràng Tiền", "Đinh Tiên Hoàng", "Hàng Bài", "Kim Mã", "Trần Hưng Đạo", "Bà Triệu", "Nguyễn Thái Học"]
                for u, v, d in G.edges(data=True):
                    street_name = str(d.get("name", ""))
                    if any(kw.lower() in street_name.lower() for kw in congest_keywords):
                        congested_edges_list.append((u, v))
                        if len(congested_edges_list) >= 25:
                            break

            for u_c, v_c in congested_edges_list:
                edge_dict = G.get_edge_data(u_c, v_c)
                if edge_dict:
                    base_l = min(float(d.get("length", 1.0)) for d in edge_dict.values())
                    traffic_weights[(u_c, v_c)] = base_l * 12.0
                    traffic_weights[(str(u_c), str(v_c))] = base_l * 12.0

        if traffic_weights and avoid_traffic:
            rd = dijkstra(G, s_node, t_node, traffic_weights=traffic_weights)
            ra = astar(G, s_node, t_node, traffic_weights=traffic_weights)
        else:
            rd, ra = rd_base, ra_base

        if rd["found"]:
            route_calculated = True
            is_rerouted = traffic_weights and avoid_traffic and (rd["nodes"] != rd_base["nodes"])
            d_pts = get_detailed_route_coords(G, rd["nodes"])
            route_coords = [tuple(st.session_state.S)] + d_pts + [tuple(st.session_state.T)]
            r_lats = [p[0] for p in route_coords]
            r_lons = [p[1] for p in route_coords]
            route_bounds = [[min(r_lats), min(r_lons)], [max(r_lats), max(r_lons)]]

# ──────────────────────────────────────────────
# TẠO BẢN ĐỒ DUY NHẤT (TỰ ĐỘNG CHUYỂN TRẠNG THÁI)
# ──────────────────────────────────────────────
map_center = center
map_zoom = 14
if route_calculated and route_bounds:
    # Tự động canh giữa theo tuyến đường
    map_center = [(route_bounds[0][0] + route_bounds[1][0])/2, (route_bounds[0][1] + route_bounds[1][1])/2]

m = folium.Map(location=map_center, zoom_start=map_zoom, tiles=current_tile, attr=current_attr)

if route_calculated and route_bounds:
    m.fit_bounds(route_bounds, padding=(30, 30))
else:
    m.fit_bounds(bounds)

# 1. Ranh giới quận
if show_boundary and gdf_boundary is not None:
    folium.GeoJson(
        gdf_boundary,
        name=f"Ranh giới {area_display}",
        style_function=lambda x: {
            "color": "#EA4335", "weight": 2.5, "dashArray": "6, 4",
            "fillColor": "#EA4335", "fillOpacity": 0.05,
        },
        tooltip=f"Địa phận {area_display}"
    ).add_to(m)

# 2. Khung xương mạng đường bộ
if show_network:
    folium.PolyLine(get_network_lines(), color="#9aa0a6", weight=1, opacity=0.35).add_to(m)

# 3. Điểm đánh dấu S và T (Chuẩn Google Marker Pin)
if st.session_state.S:
    folium.Marker(
        st.session_state.S,
        tooltip=f"<b>🟢 Điểm xuất phát (S)</b><br>{s_label}",
        icon=folium.DivIcon(
            html="""<div style="
                background:#34A853;color:white;font-weight:700;font-size:14px;
                border-radius:50%;width:32px;height:32px;line-height:32px;
                text-align:center;border:2.5px solid white;
                box-shadow:0 2px 8px rgba(0,0,0,0.35);">A</div>""",
            icon_size=(32, 32), icon_anchor=(16, 16)
        )
    ).add_to(m)

if st.session_state.T:
    folium.Marker(
        st.session_state.T,
        tooltip=f"<b>🔴 Điểm đích đến (T)</b><br>{t_label}",
        icon=folium.DivIcon(
            html="""<div style="
                background:#EA4335;color:white;font-weight:700;font-size:14px;
                border-radius:50%;width:32px;height:32px;line-height:32px;
                text-align:center;border:2.5px solid white;
                box-shadow:0 2px 8px rgba(0,0,0,0.35);">B</div>""",
            icon_size=(32, 32), icon_anchor=(16, 16)
        )
    ).add_to(m)

# 4. Vẽ đoạn đường bị ùn tắc (nếu có)
if congested_edges_list:
    for u_c, v_c in congested_edges_list:
        cong_pts = get_detailed_route_coords(G, [u_c, v_c])
        if cong_pts:
            folium.PolyLine(
                cong_pts, color="#D93025", weight=8, opacity=0.95,
                tooltip="⚠️ Đoạn đường ùn tắc nghiêm trọng! (Tốc độ giảm 90%)"
            ).add_to(m)

# 5. Nếu đã tính xong tuyến: Vẽ lộ trình lên bản đồ
if route_calculated:
    # Nếu né tắc: vẽ lộ trình cũ nét đứt để so sánh
    if is_rerouted and rd_base:
        d_orig_pts = get_detailed_route_coords(G, rd_base["nodes"])
        folium.PolyLine(
            d_orig_pts, color="#70757a", weight=4, opacity=0.5, dash_array="6, 6",
            tooltip=f"Lộ trình cũ qua điểm kẹt xe ({rd_base['distance_m']:.1f} m)"
        ).add_to(m)

    if show_both_routes:
        a_pts = get_detailed_route_coords(G, ra["nodes"])
        a_full = [tuple(st.session_state.S)] + a_pts + [tuple(st.session_state.T)]
        folium.PolyLine(route_coords, color="#1A73E8", weight=6, opacity=0.9, tooltip=f"Dijkstra: {rd['distance_m']:.1f} m").add_to(m)
        folium.PolyLine(a_full, color="#F29900", weight=4, opacity=0.9, dash_array="8, 4", tooltip=f"A*: {ra['distance_m']:.1f} m").add_to(m)
    else:
        line_color = "#1E8E3E" if is_rerouted else "#1A73E8"
        line_label = f"Tuyến né tắc thông thoáng: {rd['distance_m']:.1f} m" if is_rerouted else f"Tuyến ngắn nhất: {rd['distance_m']:.1f} m"
        folium.PolyLine(route_coords, color=line_color, weight=6, opacity=0.9, tooltip=line_label).add_to(m)

# HIỂN THỊ DUY NHẤT 1 BẢN ĐỒ TRÊN TRANG
clicked = st_folium(m, height=540, width=None, returned_objects=["last_clicked"])

# ──────────────────────────────────────────────
# NÚT ĐẶT ĐIỂM KHI CLICK TRÊN BẢN ĐỒ
# ──────────────────────────────────────────────
lat_click = lng_click = None
is_inside = True
if clicked and clicked.get("last_clicked"):
    lat_click = clicked["last_clicked"]["lat"]
    lng_click = clicked["last_clicked"]["lng"]
    if poly_boundary is not None:
        p = Point(lng_click, lat_click)
        is_inside = poly_boundary.contains(p)

if not both_set:
    col_btn_s, col_btn_t, col_info = st.columns([2, 2, 3])
    with col_btn_s:
        if st.button("📍 Đặt điểm vừa click làm Xuất phát (S)", use_container_width=True):
            if lat_click is None:
                st.warning("Hãy nhấn vào một vị trí trên bản đồ trước.")
            elif not is_inside:
                st.error(f"Điểm nhấn nằm ngoài địa phận {area_display}.")
            else:
                st.session_state.S = [lat_click, lng_click]
                st.session_state.S_name = None
                st.rerun()
    with col_btn_t:
        if st.button("🏁 Đặt điểm vừa click làm Đích đến (T)", use_container_width=True):
            if lat_click is None:
                st.warning("Hãy nhấn vào một vị trí trên bản đồ trước.")
            elif not is_inside:
                st.error(f"Điểm nhấn nằm ngoài địa phận {area_display}.")
            else:
                st.session_state.T = [lat_click, lng_click]
                st.session_state.T_name = None
                st.rerun()
    with col_info:
        if lat_click:
            st.caption(f"📌 Tọa độ vừa chọn: `{lat_click:.5f}, {lng_click:.5f}` {'(Hợp lệ)' if is_inside else '(Ngoài vùng)'}")

# ──────────────────────────────────────────────
# THỐNG KÊ KẾT QUẢ TÌM ĐƯỜNG (KHI ĐÃ CÓ TUYẾN)
# ──────────────────────────────────────────────
if route_calculated:
    st.markdown("---")
    if is_rerouted:
        st.warning("⚠️ **Đã phát hiện điểm ùn tắc trên lộ trình gốc!** Bản đồ đã tự động chuyển sang tuyến đường vòng thông thoáng thay thế (đường màu xanh lá).")

    col_stat_d, col_stat_a = st.columns(2)
    saved_pct = (1 - ra["expanded"] / max(rd["expanded"], 1)) * 100

    with col_stat_d:
        st.markdown(f"""
        <div class="stat-card stat-dijkstra">
            <div class="stat-title">🔵 Thuật toán Dijkstra</div>
            <div class="stat-dist">{rd['distance_m']:.1f} <small style="font-size:1.1rem;color:#5f6368">mét</small></div>
            <div class="stat-meta">
                ⏱ Thời gian chạy: <b>{rd['time_s']*1000:.3f} ms</b> &nbsp;|&nbsp;
                🔍 Đã mở rộng: <b>{rd['expanded']} nút</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_stat_a:
        st.markdown(f"""
        <div class="stat-card stat-astar">
            <div class="stat-title">🟠 Thuật toán A* (Haversine)</div>
            <div class="stat-dist">{ra['distance_m']:.1f} <small style="font-size:1.1rem;color:#5f6368">mét</small></div>
            <div class="stat-meta">
                ⏱ Thời gian chạy: <b>{ra['time_s']*1000:.3f} ms</b> &nbsp;|&nbsp;
                🔍 Đã mở rộng: <b>{ra['expanded']} nút</b> (tiết kiệm <b>{saved_pct:.0f}%</b>)
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.success(f"✅ Hai thuật toán cho cùng độ dài tối ưu: **{rd['distance_m']:.1f} m** (~{rd['distance_m']/1000:.2f} km). Tuyến đi qua **{len(rd['nodes'])}** nút giao thông.")
elif both_set and not route_calculated:
    st.error("❌ Không tìm được tuyến đường có hướng từ S đến T (do quy tắc phân luồng đường một chiều).")
