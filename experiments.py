"""Module quản lý dữ liệu và thí nghiệm tìm đường."""
from pathlib import Path

def find_graph():
    """Trả về đường dẫn tới đồ thị đã làm sạch (hoặc đồ thị gốc nếu chưa có)."""
    clean_path = Path("data") / "area_clean.graphml"
    if clean_path.exists():
        return clean_path
    raw_path = Path("data") / "area_raw.graphml"
    if raw_path.exists():
        return raw_path
    raise FileNotFoundError(
        "Không tìm thấy đồ thị GraphML trong thư mục data/. "
        "Vui lòng chạy 'python data.py' trước để tải dữ liệu bản đồ."
    )
