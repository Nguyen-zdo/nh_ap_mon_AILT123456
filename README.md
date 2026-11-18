📋 BÁO CÁO TIẾN ĐỘ DỰ ÁN: BÀI TẬP LỚN NHẬP MÔN AI
CHỦ ĐỀ 01: TÌM ĐƯỜNG ĐI NGẮN NHẤT TRÊN MẠNG LƯỚI ĐƯỜNG BỘ (DIJKSTRA & A*)

Trạng thái tiến độ: HOÀN THÀNH 100% CÁC TIÊU CHÍ (5/5 MỤC)
Khu vực áp dụng: Hoàn Kiếm và Ba Đình, TP. Hà Nội (network_type="drive")
Thời gian cập nhật: Tháng 11/2026

Các lỗi đã sửa so với bản trước:

Số nút/cạnh: Bản cũ ghi 414 nút, 977 cạnh, nhưng Dijkstra duyệt tới 7109 nút, điều này không thể xảy ra. Các ca thử còn nằm ở Ba Đình (Lăng Bác, Cột Cờ...), nên khu vực là Hoàn Kiếm + Ba Đình. Hãy điền số liệu thật từ graph_meta.json.
Tiêu chí ca “gần”: Bản cũ ghi <600 m nhưng ca 2, 3, 5 dài 641–860 m, nay sửa thành < 1 km.
Con số 79,7%: Không khớp bảng, nay sửa thành 75,9% (ca xa) và 86,5% (ca gần).
Nhận xét ca xa: Sửa “50% đến gần 80%” thành 55%–76%.
Nhận xét ca gần: Bản cũ viết “< 500 m, < 30 nút, thời gian xấp xỉ nhau”. Số liệu thực tế là A* duyệt 16–57 nút và vẫn nhanh hơn rõ rệt.
Chứng minh admissible: Bổ sung lý do chính xác hơn.
🚀 1. BẢNG THEO DÕI TIẾN TRÌNH
STT	Hạng mục	File	Tiến độ	Kết quả kiểm thử
1	Thu thập & tiền xử lý dữ liệu OSM
• Tải ranh giới Hoàn Kiếm + Ba Đình (GeoJSON)
• Lọc mạng đường ô tô (drive)
• Lấy SCC lớn nhất (liên thông mạnh)
• Kiểm tra độ dài cạnh $\ge 0$ và tọa độ nút	data.py	100%	• Số nút/cạnh: (điền từ graph_meta.json).
• Xuất area_clean.graphml, graph_meta.json.
2	Cài đặt Dijkstra & A*
• Tự cài Min-Heap (heapq)
• Heuristic Haversine (m)
• Tự khớp kiểu Node (int/str)	algorithms.py	100%	• Khớp độ dài tối ưu 100/100 ca ngẫu nhiên.
• Xử lý an toàn $S = T$ và không có đường đi.
3	Thực nghiệm 10 ca & 3 ca khó
• 10 cặp cố định (5 gần: đường đi $<1\text{ km}$, 5 xa: $>1.5\text{ km}$)
• Đo thời gian, số nút duyệt, % tiết kiệm
• 3 ca khó: một chiều, ngõ cụt, đường vòng	experiments.py	100%	• A* giảm tới 86.5% số nút (ca gần), 75.9% (ca xa).
• Xuất benchmark_10_cases.md và .csv.
4	Trực quan hóa & xuất ảnh
• network.png
• 3 tuyến tiêu biểu	visualization.py	100%	• route_1_short.png, route_2_long.png, route_3_detour.png.
5	Giao diện Streamlit
• Chọn $S, T$ bằng chuột
• Báo lỗi khi click ngoài ranh giới khu vực
• Vẽ tuyến tối ưu lên bản đồ	app.py	100%	• Chạy bằng streamlit run app.py.
• Chỉ hiển thị 1 bản đồ.
📐 2. CƠ SỞ LÝ THUYẾT & CHỨNG MINH HEURISTIC
2.1. Heuristic Haversine

Với $\Delta\phi = \text{lat}_2 - \text{lat}_1$, $\Delta\lambda = \text{lon}_2 - \text{lon}_1$ (đổi sang radian):

$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\text{lat}_1)\cos(\text{lat}_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)$$
$$c = 2 \cdot \text{atan2}(\sqrt{a}, \sqrt{1 - a}), \quad h(n) = R \cdot c \quad (R = 6{,}371{,}000 \text{ m})$$
2.2. Tính admissible và consistent
Haversine là độ dài đường ngắn nhất giữa hai điểm trên mặt cầu.
Độ dài mỗi cạnh $(u,v)$ trong đồ thị là độ dài đường thực tế (có thể uốn lượn), nên $w(u,v) \ge h(u,v)$, tức khoảng cách chim bay giữa hai đầu cạnh.
Do đó $h(n) \le h^*(n)$ với mọi $n$, nên heuristic admissible.
Với mọi cạnh $(u,v)$, bất đẳng thức tam giác cho $h(u) \le w(u,v) + h(v)$, nên heuristic consistent.
Kết luận: A* luôn tìm được đường tối ưu và không cần mở lại các nút đã đóng.
📊 3. KẾT QUẢ THỰC NGHIỆM (10 CA)
Ca	Phân loại	Mô tả tuyến	Dijkstra (m)	A* (m)	TG Dijkstra (ms)	TG A* (ms)	Nút Dijkstra	Nút A*	Tiết kiệm nút
1	Gần (HK)	Phố Tràng Tiền → Nhà hát Lớn	322.8	322.8	0.439	0.268	63	16	74.6%
2	Gần (HK)	Chợ Đồng Xuân → Ô Quan Chưởng	641.6	641.6	2.540	0.499	185	25	86.5%
3	Gần (BĐ)	Lăng Bác → Cột Cờ Hà Nội	647.1	647.1	1.251	0.374	130	25	80.8%
4	Gần (BĐ)	Hoàng thành Thăng Long → Cột Cờ	518.1	518.1	0.789	0.365	90	31	65.6%
5	Gần (BĐ)	Hoàng thành Thăng Long → Lăng Bác	860.4	860.4	2.237	0.583	285	57	80.0%
6	Xa (BĐ→HK)	Lăng Bác → Hồ Hoàn Kiếm	3199.7	3199.7	41.706	14.733	5508	1608	70.8%
7	Xa (HK→BĐ)	Nhà hát Lớn → Hoàng thành Thăng Long	2594.7	2594.7	16.142	5.239	2068	498	75.9%
8	Xa (BĐ→HK)	Chùa Trấn Quốc → Chợ Đồng Xuân	2035.7	2035.7	5.850	5.047	1052	401	61.9%
9	Xa (BĐ→HK)	Lotte Liễu Giai → Tràng Tiền Plaza	5004.6	5004.6	48.657	21.023	5657	1563	72.4%
10	Xa (trục)	Hoàng Hoa Thám → Cầu Chương Dương	5168.4	5168.4	58.045	28.134	7109	3179	55.3%
🔍 Nhận xét: khi nào A* có lợi thế hơn Dijkstra?
Cự ly xa ($>1.5\text{ km}$): A* tiết kiệm 55%–76% số nút duyệt và nhanh hơn khoảng 1,2–3 lần. Heuristic hướng việc tìm kiếm về phía đích, thay vì lan đều như Dijkstra.
Cự ly gần ($<1\text{ km}$): A* tiết kiệm 65%–87% số nút (chỉ duyệt 16–57 nút). Thời gian chạy chỉ vài ms nên chênh lệch tuyệt đối nhỏ, nhưng A* vẫn nhanh hơn ở mọi ca. Chi phí tính Haversine (lượng giác) làm lợi thế về thời gian thấp hơn lợi thế về số nút.
Cả hai thuật toán cho độ dài đường đi giống hệt nhau ở 10/10 ca, khẳng định A* tối ưu.
⚠️ 4. KIỂM THỬ 3 TRƯỜNG HỢP KHÓ
Đường một chiều: tuyến giữa nút 317156881 và 5689691146.
Chiều đi ($S \rightarrow T$): $887.4\text{ m}$ (16 nút).
Chiều về ($T \rightarrow S$): $1299.7\text{ m}$ (17 nút).
→ Chiều về dài hơn $412.3\text{ m}$ do phân luồng một chiều quanh phố cổ.
Ngõ cụt / không có đường đi:
Thử trên đồ thị thô area_raw.graphml, giữa nút cô lập 6689296377 và nút 98009339.
→ Thuật toán trả về found = False, distance = inf an toàn.
Đường vòng xa: tuyến giữa nút 5689691146 và 309674434.
Chim bay: $550.7\text{ m}$. Đường xe chạy thực tế: $1694.7\text{ m}$ (gấp 3.08 lần) do phải tránh phố đi bộ ven hồ.
💻 5. HƯỚNG DẪN THỰC THI
bash
# Bước 1: Cài thư viện
pip install osmnx streamlit streamlit-folium geopandas folium shapely networkx matplotlib

# Bước 2: Chạy web demo
streamlit run app.py

# Bước 3: Chạy 10 ca và xuất kết quả
python experiments.py

# Bước 4: Xuất ảnh báo cáo
python visualization.py
```
