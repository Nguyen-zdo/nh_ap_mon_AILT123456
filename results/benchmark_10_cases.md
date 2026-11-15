# Bảng kết quả so sánh Dijkstra và A* (10 ca thử nghiệm)

| Ca | Phân loại | Mô tả tuyến | Dijkstra (m) | A* (m) | Thời gian Dijkstra (ms) | Thời gian A* (ms) | Nút duyệt Dijkstra | Nút duyệt A* | Tiết kiệm nút (%) |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Gần | Đoạn ngắn phố Hàng Gai | 137.5 | 137.5 | 0.106 | 0.062 | 11 | 4 | 63.6% |
| 2 | Gần | Nội bộ khu dân cư Cửa Nam | 251.5 | 251.5 | 0.151 | 0.086 | 41 | 19 | 53.7% |
| 3 | Gần | Giao lộ Hàng Gai - Lương Văn Can | 420.4 | 420.4 | 0.253 | 0.081 | 67 | 13 | 80.6% |
| 4 | Gần | Khu vực ven hồ Hoàn Kiếm | 431.6 | 431.6 | 0.090 | 0.053 | 29 | 12 | 58.6% |
| 5 | Gần | Phố Tràng Tiền - Nhà hát Lớn | 523.9 | 523.9 | 0.463 | 0.124 | 100 | 20 | 80.0% |
| 6 | Xa | Phía Bắc sang phía Nam quận | 1599.8 | 1599.8 | 4.240 | 0.831 | 1210 | 147 | 87.9% |
| 7 | Xa | Đông Bắc xuống Tây Nam Hoàn Kiếm | 1655.6 | 1655.6 | 4.093 | 1.541 | 959 | 278 | 71.0% |
| 8 | Xa | Cửa Nam đi cầu Chương Dương | 1706.1 | 1706.1 | 7.126 | 1.440 | 1877 | 304 | 83.8% |
| 9 | Xa | Trục xuyên tâm Hoàn Kiếm | 2119.5 | 2119.5 | 9.606 | 2.673 | 2608 | 511 | 80.4% |
| 10 | Xa | Hai góc đối diện toàn quận (~3km) | 2942.8 | 2942.8 | 9.360 | 4.383 | 2387 | 798 | 66.6% |
