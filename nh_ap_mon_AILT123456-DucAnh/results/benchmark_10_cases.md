# Bảng kết quả so sánh Dijkstra và A* (10 ca thử nghiệm)

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
