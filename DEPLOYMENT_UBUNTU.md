# HƯỚNG DẪN TRIỂN KHAI HỆ THỐNG CMMS TRÊN UBUNTU 22.04 (DOCKER)

Hệ thống này được thiết kế để chạy trong môi trường Docker Compose, bao gồm 1 container cho Web (Flask) và 1 container cho Database (SQL Server 2022 Linux).

## 1. Thành phần hệ thống
- **Web App**: Flask (Python 3.12) - Chạy trên cổng 80 (ngoài) / 5000 (trong).
- **Database**: Microsoft SQL Server 2022 (Linux) - Chạy trên cổng 1433.

## 2. Các bước chuẩn bị dữ liệu (Từ máy Windows cũ)

### Bước A: Backup dữ liệu trên Windows
1. Mở SQL Server Management Studio (SSMS).
2. Chuột phải vào Database `CMMS` -> Tasks -> Back Up...
3. Lưu file backup với tên `CMMS.bak` vào thư mục của dự án (ví dụ: `C:\CMMS\backup\CMMS.bak`).

### Bước B: Nén toàn bộ mã nguồn
Nén toàn bộ thư mục `C:\CMMS` thành file `CMMS_System.zip` (đảm bảo bao gồm cả thư mục `backup` vừa tạo).

## 3. Triển khai trên Ubuntu 22.04

### Bước 1: Cài đặt Docker & Docker Compose
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

### Bước 2: Giải nén mã nguồn
Sao chép file `CMMS_System.zip` lên máy chủ Ubuntu và giải nén:
```bash
unzip CMMS_System.zip -d CMMS
cd CMMS
```

### Bước 3: Khởi chạy hệ thống lần đầu
```bash
sudo docker-compose up -d --build
```

### Bước 3b: Đồng bộ phân quyền RBAC (sau khi DB đã có dữ liệu)

**Trong container** (khuyến nghị):

```bash
docker compose exec web python fix_permissions.py
docker compose exec web python setup_rbac.py
```

**Trên máy host** (cần virtualenv — `python3` thường không có Flask):

```bash
cd ~/cmms
python3 -m venv myvenv
source myvenv/bin/activate
pip install -r requirements.txt
python fix_permissions.py
python setup_rbac.py
```

Sau đó gán role cho user trong UI và **đăng nhập lại**.

### Bước 4: Restore dữ liệu vào SQL Server Docker
Sau khi các container đã chạy, thực hiện lệnh sau để restore file `.bak`:

1. Chờ khoảng 30 giây để SQL Server khởi động xong.
2. Chạy lệnh restore (thay đổi mật khẩu nếu bạn đã đổi trong docker-compose):
```bash
sudo docker exec -it cmms_db /opt/mssql-tools/bin/sqlcmd \
   -S localhost -U sa -P "cmms@Admin123" \
   -Q "RESTORE DATABASE CMMS FROM DISK = '/var/opt/mssql/backup/CMMS.bak' WITH MOVE 'CMMS' TO '/var/opt/mssql/data/CMMS.mdf', MOVE 'CMMS_log' TO '/var/opt/mssql/data/CMMS_log.ldf'"
```

## 4. Kiểm tra hệ thống
- Truy cập vào IP của máy chủ Ubuntu qua trình duyệt: `http://<IP_SERVER>`
- Tài khoản đăng nhập mặc định: Sử dụng tài khoản cũ từ hệ thống Windows.

## 5. Lưu ý quan trọng
- **Uploads**: Toàn bộ dữ liệu upload (hồ sơ, hợp đồng) được lưu trữ bền vững tại thư mục `static/uploads` trên máy chủ Ubuntu thông qua Docker Volumes.
- **Biến môi trường**: Nếu muốn thay đổi cấu hình, chỉnh sửa trực tiếp trong file `docker-compose.yml`.
- **Driver**: Ứng dụng sử dụng `ODBC Driver 18 for SQL Server` với cấu hình `TrustServerCertificate=yes` để đảm bảo kết nối nội bộ trong Docker ổn định.
