# Hướng Dẫn Cài Đặt Hệ Thống Trên Server Mới

## Yêu cầu Hệ thống
- Hệ điều hành: Windows Server / Windows 10/11
- Microsoft SQL Server (Hoặc quyền truy cập mạng đến server cơ sở dữ liệu)
- Tùy chọn: IIS (nếu triển khai qua wfastcgi)

## 1. Cài đặt Python
1. Tải Python (phiên bản khuyên dùng: 3.10 hoặc 3.11) từ trang chủ [python.org](https://www.python.org/downloads/).
2. Trong lúc cài đặt, hãy đảm bảo **Tích chọn ô "Add Python to PATH"** ở màn hình đầu tiên.

## 2. Cài đặt ODBC Driver cho SQL Server
Ứng dụng sử dụng driver `ODBC Driver 18 for SQL Server` để kết nối cơ sở dữ liệu.
1. Tải **Microsoft ODBC Driver 18 for SQL Server** tại: [Download ODBC Driver](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
2. Chạy file cài đặt và làm theo hướng dẫn.

## 3. Tải Source Code (Mã nguồn)
1. Copy toàn bộ thư mục mã nguồn (`CMMS`) lên server.
2. Mở Command Prompt (cmd) hoặc PowerShell tại thư mục `CMMS`.

## 4. Tạo Môi trường ảo (Virtual Environment)
Môi trường ảo giúp các gói thư viện không bị xung đột với các ứng dụng khác trên Server.
```powershell
# Tạo môi trường ảo có tên "myvenv"
python -m venv myvenv

# Kích hoạt môi trường ảo
myvenv\Scripts\activate
```
*(Nếu bạn thấy `(myvenv)` ở đầu dòng lệnh, bạn đã kích hoạt thành công).*

## 5. Cài đặt các thư viện (Dependencies)
Với môi trường ảo đang được kích hoạt:
```powershell
pip install -r requirements.txt
```

## 6. Cấu hình Cơ sở dữ liệu
Nếu database được đặt trên server mới hoặc server khác:
1. Đảm bảo SQL Server đang chạy và tài khoản đăng nhập SQL Server khả dụng.
2. Mở file `app.py` trong thư mục gốc.
3. Tìm và cập nhật thông tin chuỗi kết nối (`connection_str`):
```python
connection_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER=Tên_Server_Của_Bạn_Hoặc_IP;"  
    f"DATABASE=CMMS;"
    f"UID=Tài_Khoản_SQL;"
    f"PWD=Mật_Khẩu_SQL;"                    
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)
```

## 7. Khởi chạy Ứng dụng
Để chạy thử trên môi trường phát triển:
```powershell
python run.py
```

### Dành cho Môi trường Production (Windows)
Không nên dùng lệnh `python run.py` cho Production vì Flask development server không được thiết kế cho việc chạy thực tế.
Cách 1: Sử dụng **Waitress** (Production WSGI Server cho Windows):
```powershell
pip install waitress
waitress-serve --port=5000 app:app
```

Cách 2: Cấu hình **IIS** (Internet Information Services):
Hệ thống có thể chạy trên IIS sử dụng `wfastcgi` (đã có trong `requirements.txt`). Bạn cần chạy lệnh `wfastcgi-enable` bằng quyền Administrator và cấu hình Handler Mappings trên IIS trỏ tới môi trường ảo `myvenv`.
