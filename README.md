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

| Ca | Phân loại | Mô tả tuyến đường | Dijkstra (m) | A* (m) | Thời gian Dijkstra (ms) | Thời gian A* (ms) | Nút duyệt Dijkstra | Nút duyệt A* | Nút duyệt giảm (%) |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **01** | Gần | Đoạn ngắn phố Hàng Gai | 137.5 | 137.5 | 0.048 | 0.041 | 5 | 2 | **+60.0%** |
| **02** | Gần | Nội bộ khu dân cư Cửa Nam | 251.5 | 251.5 | 0.048 | 0.039 | 14 | 9 | **+35.7%** |
| **03** | Gần | Giao lộ Hàng Gai - Lương Văn Can | 420.4 | 420.4 | 0.090 | 0.033 | 26 | 6 | **+76.9%** |
| **04** | Gần | Khu vực ven hồ Hoàn Kiếm | 431.6 | 431.6 | 0.048 | 0.033 | 17 | 8 | **+52.9%** |
| **05** | Gần | Phố Tràng Tiền - Nhà hát Lớn | 523.9 | 523.9 | 0.057 | 0.026 | 15 | 5 | **+66.7%** |
| **06** | Xa | Phía Bắc sang phía Nam quận | 1599.8 | 1599.8 | 0.789 | 0.247 | 227 | 46 | **+79.7%** |
| **07** | Xa | Đông Bắc xuống Tây Nam Hoàn Kiếm | 1694.7 | 1694.7 | 0.625 | 0.438 | 191 | 95 | **+50.3%** |
| **08** | Xa | Cửa Nam đi cầu Chương Dương | 1707.6 | 1707.6 | 0.911 | 0.646 | 270 | 138 | **+48.9%** |
| **09** | Xa | Trục xuyên tâm Hoàn Kiếm | 2423.5 | 2423.5 | 1.445 | 0.819 | 383 | 180 | **+53.0%** |
| **10** | Xa | Hai góc đối diện toàn quận (~3km) | 3029.6 | 3029.6 | 1.358 | 1.146 | 405 | 235 | **+42.0%** |

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
