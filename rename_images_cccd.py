import os
import random
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Thư mục ảnh
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}


def generate_random_cccd():
    """
    Sinh số CCCD hợp lệ 12 chữ số
    - 3 số đầu: 001 (Hà Nội) hoặc 033 (Hưng Yên)
    - 1 số tiếp theo: 0-3 (Thế kỷ 20, 21)
    - 2 số tiếp theo: Năm sinh (00 - 99)
    - 6 số cuối: random từ 000001 đến 999999
    """
    province = random.choice(["001", "033"])
    century_gender = str(random.choice([0, 1, 2, 3]))
    year = f"{random.randint(0, 99):02d}"
    random_id = f"{random.randint(1, 999999):06d}"

    return f"{province}{century_gender}{year}{random_id}"


def main():
    if not os.path.exists(IMAGES_DIR):
        logger.error(f"Thư mục {IMAGES_DIR} không tồn tại!")
        return

    # Quét đệ quy (recursive) toàn bộ thư mục và thư mục con
    image_files = []
    for root, _, files in os.walk(IMAGES_DIR):
        for fname in files:
            if os.path.splitext(fname)[1].lower() in SUPPORTED_EXTENSIONS:
                image_files.append(os.path.join(root, fname))

    if not image_files:
        logger.warning(
            f"Không tìm thấy file ảnh nào trong {IMAGES_DIR} và các thư mục con"
        )
        return

    logger.info(f"Tìm thấy {len(image_files)} ảnh. Đang tiến hành đổi tên...")

    success_count = 0
    for file_path in image_files:
        dir_name = os.path.dirname(file_path)
        ext = os.path.splitext(file_path)[1].lower()
        new_cccd = generate_random_cccd()
        new_fname = f"{new_cccd}{ext}"
        new_path = os.path.join(dir_name, new_fname)

        # Tránh trùng tên ngẫu nhiên
        while os.path.exists(new_path):
            new_cccd = generate_random_cccd()
            new_fname = f"{new_cccd}{ext}"
            new_path = os.path.join(dir_name, new_fname)

        try:
            os.rename(file_path, new_path)
            success_count += 1
        except Exception as e:
            logger.error(f"Lỗi khi đổi tên file {file_path}: {e}")

    logger.info(
        f"Hoàn tất đổi tên {success_count}/{len(image_files)} ảnh thành số CCCD chuẩn."
    )


if __name__ == "__main__":
    main()
