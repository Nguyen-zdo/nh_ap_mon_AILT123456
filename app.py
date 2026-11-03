"""Demo Streamlit: chọn hai điểm trên bản đồ, so sánh Dijkstra và A*."""
from pathlib import Path
import osmnx as ox
import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point

from algorithms import dijkstra, astar
from experiments import find_graph

st.set_page_config(page_title="Tìm đường giao hàng – Hoàn Kiếm", layout="wide")
st.title("Tìm tuyến giao hàng – Quận Hoàn Kiếm cũ")
st.caption("Dijkstra và A* trên mạng đường bộ có hướng | Chiều dài cạnh: mét")

# Danh sách nguồn bản đồ
TILES_MAP = {
    "OpenStreetMap (Nhanh & Ổn định)": {
        "tiles": "https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png",
        "attr": "&copy; OpenStreetMap contributors"
    },
    "Google Maps": {
        "tiles": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        "attr": "Google Maps"
    },
    "CartoDB Voyager": {
        "tiles": "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        "attr": "&copy; OpenStreetMap contributors &copy; CARTO"
    }
}

st.sidebar.header("Cài đặt hiển thị")
tile_choice = st.sidebar.selectbox("Kiểu bản đồ:", list(TILES_MAP.keys()), index=0)
current_tile = TILES_MAP[tile_choice]["tiles"]
current_attr = TILES_MAP[tile_choice]["attr"]

show_boundary = st.sidebar.checkbox("Hiển thị ranh giới Quận Hoàn Kiếm", value=True)
show_network = st.sidebar.checkbox("Hiển thị mạng lưới đường Hoàn Kiếm", value=True)

@st.cache_resource
def load_graph():
    return ox.load_graphml(find_graph())

@st.cache_resource
def load_boundary():
    boundary_path = Path("boundary") / "hoan_kiem_old.geojson"
    if boundary_path.exists():
        gdf = gpd.read_file(boundary_path)
        return gdf, gdf.geometry.iloc[0]
    return None, None

G = load_graph()
gdf_boundary, poly_boundary = load_boundary()

nodes = list(G.nodes)
xs = [float(G.nodes[n]["x"]) for n in nodes]
ys = [float(G.nodes[n]["y"]) for n in nodes]
center = [sum(ys)/len(ys), sum(xs)/len(xs)]
bounds = [[min(ys), min(xs)], [max(ys), max(xs)]]

st.info("📌 Chỉ chọn các điểm **bên trong ranh giới màu đỏ của Quận Hoàn Kiếm**. Nhấn vào bản đồ rồi bấm nút để xác nhận.")

if "S" not in st.session_state:
    st.session_state.S = None
if "T" not in st.session_state:
    st.session_state.T = None

def create_base_map():
    m = folium.Map(location=center, zoom_start=14, tiles=current_tile, attr=current_attr)
    m.fit_bounds(bounds)

    # 1. Vẽ ranh giới quận Hoàn Kiếm
    if show_boundary and gdf_boundary is not None:
        folium.GeoJson(
            gdf_boundary,
            name="Ranh giới Hoàn Kiếm",
            style_function=lambda x: {
                "color": "#D32F2F",
                "weight": 3.5,
                "dashArray": "5, 5",
                "fillColor": "#FF5252",
                "fillOpacity": 0.08,
            },
            tooltip="Địa phận Quận Hoàn Kiếm"
        ).add_to(m)

    # 2. Vẽ mạng lưới đường bộ Hoàn Kiếm
    if show_network:
        lines = []
        for u, v in G.edges():
            lines.append([(float(G.nodes[u]["y"]), float(G.nodes[u]["x"])),
                          (float(G.nodes[v]["y"]), float(G.nodes[v]["x"]))])
        folium.PolyLine(lines, color="#666666", weight=1.2, opacity=0.45, tooltip="Mạng đường Hoàn Kiếm").add_to(m)

    # 3. Đánh dấu điểm S và T
    if st.session_state.S:
        folium.Marker(st.session_state.S, tooltip="S – Điểm xuất phát",
                      icon=folium.Icon(color="green", icon="play")).add_to(m)
    if st.session_state.T:
        folium.Marker(st.session_state.T, tooltip="T – Điểm đích",
                      icon=folium.Icon(color="red", icon="flag")).add_to(m)
    return m

base_map = create_base_map()
clicked = st_folium(base_map, height=570, width=None, returned_objects=["last_clicked"])

# Kiểm tra điểm nhấn có trong Hoàn Kiếm không
is_inside = True
if clicked and clicked.get("last_clicked"):
    lat_click = clicked["last_clicked"]["lat"]
    lng_click = clicked["last_clicked"]["lng"]
    if poly_boundary is not None:
        p = Point(lng_click, lat_click)
        is_inside = poly_boundary.contains(p)
        if not is_inside:
            st.warning(f"⚠️ Điểm vừa nhấn ({lat_click:.4f}, {lng_click:.4f}) nằm ngoài địa phận quận Hoàn Kiếm! Vui lòng chọn điểm bên trong đường viền đỏ.")

c1, c2, c3 = st.columns(3)
if c1.button("Đặt điểm vừa nhấn làm S") and clicked.get("last_clicked"):
    if is_inside:
        st.session_state.S = [clicked["last_clicked"]["lat"], clicked["last_clicked"]["lng"]]
        st.rerun()
    else:
        st.error("Không thể đặt S ngoài địa phận Hoàn Kiếm.")

if c2.button("Đặt điểm vừa nhấn làm T") and clicked.get("last_clicked"):
    if is_inside:
        st.session_state.T = [clicked["last_clicked"]["lat"], clicked["last_clicked"]["lng"]]
        st.rerun()
    else:
        st.error("Không thể đặt T ngoài địa phận Hoàn Kiếm.")

if c3.button("Xóa S/T"):
    st.session_state.S = st.session_state.T = None
    st.rerun()

if st.session_state.S and st.session_state.T:
    s = ox.distance.nearest_nodes(G, X=st.session_state.S[1], Y=st.session_state.S[0])
    t = ox.distance.nearest_nodes(G, X=st.session_state.T[1], Y=st.session_state.T[0])
    st.write(f"Nút giao mạng đường gần nhất: S={s}, T={t}")
    if s == t:
        st.warning("Hai điểm đang được ánh xạ vào cùng một nút giao.")
    else:
        rd, ra = dijkstra(G, s, t), astar(G, s, t)
        if not rd["found"]:
            st.error("Không có tuyến đường có hướng từ S đến T.")
        else:
            st.subheader("Kết quả so sánh")
            a, b = st.columns(2)
            a.metric("Dijkstra", f"{rd['distance_m']:.1f} m",
                     f"{rd['time_s']*1000:.3f} ms")
            b.metric("A*", f"{ra['distance_m']:.1f} m",
                     f"{ra['time_s']*1000:.3f} ms")
            st.write(f"Số nút mở rộng: Dijkstra **{rd['expanded']}** · A* **{ra['expanded']}**")
            
            route_map = create_base_map()
            coords = [(float(G.nodes[n]["y"]), float(G.nodes[n]["x"])) for n in rd["nodes"]]
            folium.PolyLine(coords, color="#0055FF", weight=6, opacity=0.9, tooltip="Tuyến ngắn nhất").add_to(route_map)
            st_folium(route_map, height=570, width=None, key="route_map")
            st.caption("Hai thuật toán phải cho cùng chiều dài tối ưu; thời gian chạy có thể dao động giữa các lần.")
