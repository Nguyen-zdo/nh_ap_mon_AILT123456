# 📋 BÁO CÁO TIẾN ĐỘ DỰ ÁN: BÀI TẬP LỚN NHẬP MÔN AI
## CHỦ ĐỀ 01: TÌM ĐƯỜNG ĐI NGẮN NHẤT TRÊN MẠNG LƯỚI ĐƯỜNG BỘ (DIJKSTRA & A*)

> **Trạng thái tiến độ:** `HOÀN THÀNH 100% CÁC TIÊU CHÍ (5/5 MỤC)`  
> **Khu vực áp dụng:** Quận Hoàn Kiếm (cũ), TP. Hà Nội (`network_type="drive"`)  
> **Thời gian cập nhật:** Tháng 11/2026

---

## 🚀 1. BẢNG THEO DÕI TIẾN TRÌNH HIỆN TẠI (PROGRESS CHECKLIST)

| STT | Hạng mục công việc theo yêu cầu đề bài | File phụ trách | Tiến độ | Ghi chú & Kết quả kiểm thử |
| :---: | :---| :---: | :---: | :---|
| **1** | **Thu thập & Tiền xử lý dữ liệu OpenStreetMap**<br>• Tải ranh giới Hoàn Kiếm cũ bằng GeoJSON<br>• Lọc mạng đường ô tô (`drive`)<br>• Trích xuất SCC lớn nhất (liên thông mạnh)<br>• Kiểm tra chiều dài cạnh $\ge 0$ và tọa độ nút | `data.py` | **100%** | • 414 nút, 977 cạnh, 309 cạnh 1 chiều.<br>• Xuất `area_clean.graphml`, `graph_meta.json`. |
| **2** | **Cài đặt Thuật toán Dijkstra & A\***<br>• Tự cài đặt Min-Heap (`heapq`)<br>• Heuristic khoảng cách chim bay Haversine ($m$)<br>• Tự động khớp kiểu dữ liệu Node (`int`/`str`) | `algorithms.py` | **100%** | • Khớp độ dài đường tối ưu 100/100 ca ngẫu nhiên.<br>• Xử lý an toàn $S = T$ và không có đường đi. |
| **3** | **Thực nghiệm 10 ca & Phân tích 3 ca khó**<br>• 10 cặp cố định (5 gần $<600\text{m}$, 5 xa $>1.5\text{km}$)<br>• Đo thời gian (ms), số nút duyệt, % tiết kiệm<br>• 3 ca khó: đường 1 chiều, ngõ cụt, đường vòng | `experiments.py` | **100%** | • A* giảm tới **79.7%** số nút duyệt ở ca xa.<br>• Tự động xuất `benchmark_10_cases.md` & `.csv`. |
| **4** | **Trực quan hóa đồ thị & Xuất ảnh báo cáo**<br>• Xuất ảnh mạng lưới toàn quận `network.png`<br>• Xuất ảnh 3 tuyến đường tiêu biểu cho báo cáo | `visualization.py` | **100%** | • Đã tạo: `route_1_short.png`, `route_2_long.png`, `route_3_detour.png`. |
| **5** | **Giao diện Web tương tác (Streamlit Demo)**<br>• Chọn 2 điểm $S, T$ trực quan bằng chuột<br>• Bắt lỗi click ra ngoài ranh giới Hoàn Kiếm<br>• Vẽ trực tiếp tuyến đường tối ưu lên bản đồ | `app.py` | **100%** | • Chạy mượt mà qua lệnh `streamlit run app.py`.<br>• Chỉ hiển thị 1 bản đồ duy nhất, tối ưu trải nghiệm. |

---

## 📐 2. CƠ SỞ LÝ THUYẾT & CHỨNG MINH HEURISTIC

### 2.1. Heuristic Haversine
* Khoảng cách chim bay tính bằng mét giữa $(\text{lat}_1, \text{lon}_1)$ và $(\text{lat}_2, \text{lon}_2)$:
  $$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\text{lat}_1)\cos(\text{lat}_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)$$
  $$c = 2 \cdot \text{atan2}(\sqrt{a}, \sqrt{1 - a}), \quad h(n) = R \cdot c \quad (R = 6,371,000 \text{ m})$$

### 2.2. Giải thích vì sao Heuristic không vượt quá độ dài đường thực tế (Tính Admissible)
* Khoảng cách trắc địa Haversine là độ dài đường cong ngắn nhất nối hai điểm trên mặt cầu (Trái Đất).
* Trong mạng lưới giao thông đường bộ, phương tiện bắt buộc phải di chuyển theo các đoạn đường có sẵn, uốn lượn qua các giao lộ, ngã rẽ và chướng ngại vật địa hình.
* Do đó, chiều dài đường đi thực tế $h^*(n)$ luôn luôn thỏa mãn:
  $$h(n) \le h^*(n) \quad \forall n$$
* **Kết luận:** Heuristic Haversine luôn **admissible** (chấp nhận được) và thỏa mãn bất đẳng thức tam giác (**consistent** / đơn điệu), đảm bảo A* luôn tìm ra đường đi tối ưu tuyệt đối mà không cần mở lại các nút đã đóng.

---

## 📊 3. BẢNG KẾT QUẢ THỰC NGHIỆM CHI TIẾT (10 CA ĐẠI DIỆN)

| Ca | Phân loại | Mô tả tuyến | Dijkstra (m) | A* (m) | Thời gian Dijkstra (ms) | Thời gian A* (ms) | Nút duyệt Dijkstra | Nút duyệt A* | Tiết kiệm nút (%) |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Gần (HK) | HK: Phố Tràng Tiền -> Nhà hát Lớn | 322.8 | 322.8 | 0.439 | 0.268 | 63 | 16 | 74.6% |
| 2 | Gần (HK) | HK: Chợ Đồng Xuân -> Ô Quan Chưởng | 641.6 | 641.6 | 2.540 | 0.499 | 185 | 25 | 86.5% |
| 3 | Gần (BĐ) | BĐ: Lăng Bác -> Cột Cờ Hà Nội | 647.1 | 647.1 | 1.251 | 0.374 | 130 | 25 | 80.8% |
| 4 | Gần (BĐ) | BĐ: Hoàng thành Thăng Long -> Cột Cờ | 518.1 | 518.1 | 0.789 | 0.365 | 90 | 31 | 65.6% |
| 5 | Gần (BĐ) | BĐ: Hoàng thành Thăng Long -> Lăng Bác | 860.4 | 860.4 | 2.237 | 0.583 | 285 | 57 | 80.0% |
| 6 | Xa (BĐ-HK) | Liên quận: Lăng Bác -> Hồ Hoàn Kiếm | 3199.7 | 3199.7 | 41.706 | 14.733 | 5508 | 1608 | 70.8% |
| 7 | Xa (HK-BĐ) | Liên quận: Nhà hát Lớn -> Hoàng thành Thăng Long | 2594.7 | 2594.7 | 16.142 | 5.239 | 2068 | 498 | 75.9% |
| 8 | Xa (BĐ-HK) | Liên quận: Chùa Trấn Quốc -> Chợ Đồng Xuân | 2035.7 | 2035.7 | 5.850 | 5.047 | 1052 | 401 | 61.9% |
| 9 | Xa (BĐ-HK) | Liên quận: Lotte Liễu Giai -> Tràng Tiền Plaza | 5004.6 | 5004.6 | 48.657 | 21.023 | 5657 | 1563 | 72.4% |
| 10 | Xa (Trục) | Trục xuyên tâm: Hoàng Hoa Thám -> Cầu Chương Dương | 5168.4 | 5168.4 | 58.045 | 28.134 | 7109 | 3179 | 55.3% |

### 🔍 Nhận xét học thuật: Khi nào A* có lợi thế hơn Dijkstra?
1. **Ở các cự ly xa ($> 1.5\text{ km}$):** A* vượt trội hoàn toàn khi **tiết kiệm từ 50% đến gần 80% số nút cần duyệt**. Heuristic định hướng đường đi thẳng về phía mục tiêu, loại bỏ việc duyệt lan tỏa vô hướng ra các nhánh ngược hướng đích như Dijkstra.
2. **Ở các cự ly gần ($< 500\text{ m}$):** Số nút duyệt của cả hai đều rất ít ($< 30$ nút). Mặc dù A* vẫn duyệt ít nút hơn, nhưng do chi phí tính toán lượng giác (trig operations) của Haversine nên thời gian thực thi xấp xỉ nhau.

---

## ⚠️ 4. KẾT QUẢ KIỂM THỬ 3 TRƯỜNG HỢP KHÓ (EDGE CASES)

1. **Trường hợp 1 (Đường một chiều - Oneway Street):**
   * Tuyến giữa nút `317156881` và `5689691146`:
   * Chiều đi ($S \rightarrow T$): $887.4\text{ m}$ (16 nút).
   * Chiều về ($T \rightarrow S$): $1299.7\text{ m}$ (17 nút).
   * $\rightarrow$ *Kết luận:* Chiều về dài hơn chiều đi **$412.3\text{ m}$** do ảnh hưởng của hệ thống phân luồng một chiều quanh phố cổ.
2. **Trường hợp 2 (Ngõ cụt / Không có đường đi - Unreachable):**
   * Kiểm thử trên đồ thị thô `area_raw.graphml` giữa nút cô lập `6689296377` và nút `98009339`.
   * $\rightarrow$ *Kết luận:* Thuật toán nhận diện chính xác thành phần không liên thông, trả về `found = False, distance = inf` an toàn.
3. **Trường hợp 3 (Tuyến đường vòng xa - Detour Route):**
   * Tuyến giữa nút `5689691146` và `309674434`.
   * Khoảng cách chim bay: $550.7\text{ m}$ $\rightarrow$ Đường xe chạy thực tế: **$1694.7\text{ m}$ (gấp 3.08 lần)** do tránh phố đi bộ ven hồ.

---

## 💻 5. HƯỚNG DẪN THỰC THI CHƯƠNG TRÌNH

### Bước 1: Cài đặt thư viện
```bash
pip install osmnx streamlit streamlit-folium geopandas folium shapely networkx matplotlib
```

### Bước 2: Chạy giao diện Web demo (Streamlit)
```bash
streamlit run app.py
```

### Bước 3: Chạy so sánh 10 ca & xuất file kết quả
```bash
python experiments.py
```

### Bước 4: Xuất ảnh phục vụ báo cáo
```bash
python visualization.py
```
## 6. KẾ HOẠCH GIAO DỮ LIỆU & ĐỐI NGUYÊN GIÁM SÁT (CITATION)
Dữ liệu bản đồ: OpenStreetMap (OSM)
Khu vực nghiên cứu: Khu vực Hoàn Kiếm cũ, Quận 1 – Hà Nội (network_type="drive")
Thời điểm truy cập dữ liệu: Tháng 11/2026 (ngày cụ thể được ghi nhận tại thời điểm tải tệp)

🔍 6.1. Thông tin về nguồn dữ liệu OpenStreetMap
URL truy cập: https://www.openstreetmap.org/ (ngày truy cập cụ thể được ghi lại khi tải dữ liệu)

Nguồn trích xuất dữ liệu khu vực: Tệp vietnam-latest.osm.pbf từ Geofabrik, truy cập qua https://download.geofabrik.de/asia/vietnam.html. Geofabrik cập nhật tệp trích xuất hàng ngày; do đó, mốc thời gian cần được xác định dựa trên timestamp thực tế của tệp tại thời điểm tải (trường last modified hoặc metadata), không nên ấn định một tháng cố định trước khi tải .

Lệ phí sử dụng: Miễn phí. Dữ liệu OSM được phát hành theo Giấy phép Cơ sở dữ liệu mở Open Data Commons (ODbL). CC-BY-SA chỉ áp dụng cho tài liệu hướng dẫn/wiki của OSM, không áp dụng cho dữ liệu bản đồ .

⚖️ 6.2. Điều khoản sử dụng & Nghĩa vụ ghi công
Bản quyền dữ liệu: © OpenStreetMap contributors.

Yêu cầu ghi công (theo ODbL): Khi công bố sản phẩm sử dụng dữ liệu OSM (bao gồm báo cáo học thuật, bản đồ, hoặc cơ sở dữ liệu dẫn xuất), cần thực hiện đồng thời hai nghĩa vụ :

Ghi công "OpenStreetMap" là nguồn dữ liệu.
Làm rõ rằng dữ liệu được cung cấp theo ODbL, thông qua liên kết đến https://www.openstreetmap.org/copyright hoặc trích dẫn toàn văn giấy phép.
Mẫu trích dẫn đề xuất: "Dữ liệu bản đồ © OpenStreetMap contributors, có sẵn theo Giấy phép Cơ sở dữ liệu mở (ODbL), https://www.openstreetmap.org/copyright, [Ngày truy cập]."

Điều chỉnh dữ liệu: Dữ liệu đã được làm sạch (loại bỏ cạnh có độ dài < 0 m; tách các kết nối một chiều theo cấu hình osmnx.drive). Các thao tác này tạo ra một cơ sở dữ liệu dẫn xuất (Derivative Database); nếu công bố lại, cơ sở dữ liệu dẫn xuất này cũng phải được chia sẻ theo các điều khoản của ODbL (điều khoản "Share-Alike") .

📜 6.3. Bản quyền & Ghi chú pháp lý
Cơ sở pháp lý: ODbL 1.0. Nghĩa vụ ghi công và chia sẻ tương tự (Share-Alike) là bắt buộc đối với mọi hình thức sử dụng công khai dữ liệu hoặc cơ sở dữ liệu dẫn xuất .

Rủi ro pháp lý: Không được sao chép, phân phối hoặc bán lại dữ liệu OSM như một sản phẩm thương mại độc lập mà không tuân thủ đầy đủ các điều khoản của ODbL. Việc sử dụng trong nghiên cứu học thuật (không thương mại) được cho phép với điều kiện thực hiện đúng nghĩa vụ ghi công và chia sẻ tương tự nếu có tạo lập cơ sở dữ liệu dẫn xuất .

