"""
putimg_orcl.py
--------------
Đọc tất cả ảnh trong thư mục `images/`, đọc dạng bytes nhị phân,
rồi INSERT/MERGE vào bảng Images của Oracle Database (trường ContentImg kiểu BLOB).

Đã tối ưu hóa sử dụng Connection Pool và ThreadPoolExecutor để xử lý song song,
hỗ trợ tải lượng lớn dữ liệu (e.g. 20,000 files).
"""

import os
import logging
import oracledb
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

# ---------------------------------------------------------------------------
# Cấu hình Oracle
# ---------------------------------------------------------------------------
ORACLE_CONFIG = {
    "host": "host.docker.internal",
    "port": 1521,
    "service_name": "XEPDB1",
    "user": "IMGDATATEST",
    "password": "Nam12345",
}

# ---------------------------------------------------------------------------
# Thư mục ảnh
# ---------------------------------------------------------------------------
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}

# Cấu hình số luồng
MAX_WORKERS = 10

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Connection pool toàn cục
db_pool = None


# ---------------------------------------------------------------------------
# Hàm tiện ích
# ---------------------------------------------------------------------------
def image_to_bytes(file_path: str) -> bytes:
    """Đọc file ảnh và trả về dữ liệu nhị phân (bytes)."""
    with open(file_path, "rb") as f:
        return f.read()


def get_image_files(directory: str) -> list:
    """Quét đệ quy (recursive) toàn bộ thư mục và thư mục con giống rename_images_cccd.py"""
    if not os.path.exists(directory):
        logger.error("Thư mục %s không tồn tại!", directory)
        return []

    # Quét đệ quy (recursive) toàn bộ thư mục và thư mục con
    image_files = []
    for root, _, files in os.walk(directory):
        for fname in files:
            if os.path.splitext(fname)[1].lower() in SUPPORTED_EXTENSIONS:
                full_path = os.path.join(root, fname)
                cccd = os.path.splitext(fname)[0]
                image_files.append((cccd, full_path))

    if not image_files:
        logger.warning(
            "Không tìm thấy file ảnh nào trong %s và các thư mục con", directory
        )
        return []

    logger.info(
        "Tìm thấy %d ảnh trong thư mục: %s (bao gồm thư mục con)",
        len(image_files),
        directory,
    )
    return image_files


def init_db_pool():
    """Khởi tạo Connection Pool."""
    global db_pool
    dsn = oracledb.makedsn(
        ORACLE_CONFIG["host"],
        ORACLE_CONFIG["port"],
        service_name=ORACLE_CONFIG["service_name"],
    )
    # Khởi tạo pool với số lượng kết nối tương đương số luồng
    db_pool = oracledb.create_pool(
        user=ORACLE_CONFIG["user"],
        password=ORACLE_CONFIG["password"],
        dsn=dsn,
        min=2,
        max=MAX_WORKERS,
        increment=2,
    )


def process_single_image(image_info):
    """Xử lý insert 1 ảnh, dùng cho hàm map của ThreadPoolExecutor."""
    cccd, file_path = image_info
    fname = os.path.basename(file_path)

    sql = """
        BEGIN
            INSERT INTO Images (CCCD, FileName, ContentImg, CreatedAt)
            VALUES (:cccd, :filename, :content_img, SYSTIMESTAMP);
        EXCEPTION
            WHEN DUP_VAL_ON_INDEX THEN
                UPDATE Images
                SET FileName = :filename,
                    ContentImg = :content_img,
                    CreatedAt = SYSTIMESTAMP
                WHERE CCCD = :cccd;
        END;
    """

    try:
        content_bytes = image_to_bytes(file_path)
        with db_pool.acquire() as conn:
            with conn.cursor() as cursor:
                # Báo cho driver biết content_img là kiểu BLOB nhị phân
                cursor.setinputsizes(content_img=oracledb.DB_TYPE_BLOB)
                cursor.execute(
                    sql,
                    {
                        "cccd": cccd,
                        "filename": fname,
                        "content_img": content_bytes,
                    },
                )
            conn.commit()
        return (True, cccd, fname, len(content_bytes), None)
    except Exception as e:
        return (False, cccd, fname, 0, str(e))


def insert_images_concurrent(images: list) -> None:
    """Xử lý song song toàn bộ ảnh bằng ThreadPool."""
    success = 0
    failed = 0

    logger.info(f"Bắt đầu đẩy vào DB sử dụng {MAX_WORKERS} luồng...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_single_image, img) for img in images]

        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            is_success, cccd, fname, size, err = future.result()

            if is_success:
                logger.debug(
                    "  OK CCCD=%-20s | FileName=%-30s | Size=%d bytes",
                    cccd,
                    fname,
                    size,
                )
                success += 1
            else:
                logger.error("  FAIL CCCD=%-20s | Lỗi: %s", cccd, err)
                failed += 1

            # Log tiến độ định kỳ
            if i % 1000 == 0 or i == len(images):
                logger.info(
                    f"Tiến độ: {i}/{len(images)} (Thành công: {success}, Lỗi: {failed})"
                )

    logger.info("Hoàn thành: %d thành công, %d thất bại.", success, failed)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    logger.info("=== Bắt đầu import ảnh vào Oracle ===")

    try:
        logger.info("Khởi tạo Database Connection Pool...")
        init_db_pool()
        logger.info("Khởi tạo Pool thành công.")
    except oracledb.DatabaseError as e:
        logger.error("Không thể kết nối Oracle: %s", e)
        return

    images = get_image_files(IMAGES_DIR)
    if not images:
        logger.warning("Không có ảnh nào để xử lý. Kết thúc.")
        return

    # Import đa luồng
    insert_images_concurrent(images)

    # Đóng pool
    if db_pool:
        db_pool.close()

    logger.info("=== Kết thúc ===")


if __name__ == "__main__":
    main()
