FROM python:3.11-slim

# Không ghi .pyc và log flush ngay lập tức
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Cài thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source (trừ những gì trong .dockerignore)
COPY . .

# Thư mục ảnh sẽ được mount từ ngoài máy HOST vào /app/images lúc chạy
# docker run -v /path/to/images:/app/images data-source:v1 <script> [args]
# Mặc định không có CMD cứng — người dùng chọn script khi run

# --- Ví dụ chạy ---
# Đổi tên ảnh thành số CCCD:
#   docker run --rm -v D:/images:/app/images data-source:v1 python rename_images_cccd.py
#
# Đẩy ảnh vào Oracle (cần cấu hình ORACLE_CONFIG trong putimg_orcl.py hoặc qua -e):
#   docker run --rm \
#     -v D:/images:/app/images \
#     --network host \
#     data-source:v1 python putimg_orcl.py
