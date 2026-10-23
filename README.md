# Data Source — Cách chạy

## Setup



1. Đặt ảnh vào thư mục `images/`. tải ảnh từ link sau (https://drive.google.com/file/d/1q5XdWRBeXTfovy2a3Ld4WzhXnvgVCS3X/view?usp=sharing)

2. Sửa thông tin kết nối Oracle trong `putimg_orcl.py` nếu cần:
   ```python
   ORACLE_CONFIG = {
       "host": "localhost",
       "port": 1521,
       "service_name": "XEPDB1",
       "user": "IMGDATA",
       "password": "Nam12345",
   }
   ```
3. Build image:
   ```powershell
   docker compose build
   ```

## Chạy

**Bước 1 — Đổi tên ảnh thành số CCCD:**
```powershell
docker compose run --rm rename-images
```

**Bước 2 — Đẩy ảnh lên Oracle:**
```powershell
docker compose run --rm put-images-oracle
```

**Hoặc chạy cả 2 bước liên tiếp:**
```powershell
docker compose up --build
```

## Lỗi thường gặp

| Lỗi | Cách xử lý |
|---|---|
| `ORA-12541: No listener` | Oracle chưa khởi động, chờ thêm 1-2 phút |
| `Không tìm thấy file ảnh` | Kiểm tra lại thư mục `images/` |
| `ORA-01017: invalid username/password` | Sửa lại `ORACLE_CONFIG` trong `putimg_orcl.py` |
