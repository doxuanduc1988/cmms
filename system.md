# Tài Liệu Kiến Trúc Hệ Thống CMMS

Hệ thống CMMS (Computerized Maintenance Management System) kết hợp Quản lý Nhân sự & Chấm công.

---

## 1. Công nghệ sử dụng (Tech Stack)

| Thành phần          | Công nghệ                                    |
|---------------------|-----------------------------------------------|
| Backend Framework   | Python Flask 3.1.2                            |
| Database ORM        | Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0.44     |
| Database Provider   | Microsoft SQL Server                          |
| Database Driver     | pyodbc (ODBC Driver 18 for SQL Server)        |
| Authentication      | Flask-Login 0.6.3, Flask-Bcrypt 1.0.1         |
| Frontend/Templating | Jinja2 3.1.6 (HTML/CSS/JS)                    |
| Xử lý Excel         | pandas 2.3.3, openpyxl 3.1.5                  |
| Tạo PDF             | weasyprint 66.0, pdfkit 1.0.0                 |
| WSGI (Production)   | wfastcgi 3.0.0 (IIS) hoặc Waitress           |

---

## 2. Cấu trúc Thư mục

```
CMMS/
├── app.py                  # File chính: cấu hình Flask, DB, đăng ký Blueprints
├── run.py                  # Script khởi chạy cho dev (python run.py)
├── config.py               # Hằng số cấu hình (thư mục upload, flags)
├── extensions.py           # Khởi tạo các extension dùng chung (db, login_manager, bcrypt)
├── init_db.py              # Script tạo bảng trong DB (db.create_all)
├── requirements.txt        # Danh sách thư viện Python cần cài
├── setup_instructions.md   # Hướng dẫn triển khai server mới
│
├── models/                 # Định nghĩa các ORM Models (ánh xạ bảng SQL Server)
│   ├── __init__.py         # Re-export tất cả models chính
│   ├── hr/                 # Models nhân sự (Employee, Department, HRProfile...)
│   ├── attendance/         # Models chấm công (Attendance, Shift, Approval...)
│   └── procurement/        # Models mua sắm
│
├── routes/                 # Controllers (Flask Blueprints)
│   ├── auth.py             # Đăng nhập / Đăng xuất
│   ├── account.py          # Quản lý tài khoản
│   ├── hr.py               # Quản lý hồ sơ nhân sự
│   ├── employees.py        # CRUD nhân viên
│   ├── departments.py      # CRUD phòng ban
│   ├── roles.py            # CRUD vai trò
│   ├── permissions.py      # Quản lý quyền
│   ├── procurement.py      # Mua sắm / Đấu thầu
│   ├── attendance/         # Chấm công (tạo, sửa, duyệt, thống kê...)
│   │   ├── stats/          # Biểu đồ & thống kê chấm công
│   │   └── ...
│   └── crew_definitions/   # Định nghĩa tổ/ca
│
├── utils/                  # Hàm tiện ích dùng chung
│   ├── decorators.py       # Decorator phân quyền (@check_permission)
│   ├── permission_utils.py # Hàm kiểm tra quyền (has_permission)
│   ├── auth_utils.py       # Hàm xác thực (login_required tùy chỉnh)
│   ├── attendance_utils.py # Tính giờ công, OT
│   └── ...
│
├── templates/              # Giao diện HTML (Jinja2)
├── static/                 # Tệp tĩnh (CSS, JS, hình ảnh)
├── uploads/                # Thư mục upload file
├── logs/                   # Log hệ thống
└── myvenv/                 # Virtual environment (Python)
```

---

## 3. Kiến trúc ứng dụng

### 3.1 Entry Point
- **`app.py`**: File khởi tạo chính. Cấu hình Flask app, kết nối DB, đăng ký tất cả 46 Blueprints.
- **`run.py`**: Dùng cho môi trường phát triển (`python run.py` → debug mode).

### 3.2 Extensions (`extensions.py`)
Khởi tạo các đối tượng extension dùng chung để tránh circular import:
- `db` = SQLAlchemy()
- `login_manager` = LoginManager()
- `migrate` = Migrate()
- `bcrypt` = Bcrypt()

### 3.3 Blueprint Pattern
Mỗi module chức năng là một Flask Blueprint riêng biệt, được đăng ký tập trung trong `app.py` thông qua danh sách `_blueprints`.

---

## 4. Quản lý Quyền Truy Cập (RBAC)

Hệ thống sử dụng cơ chế phân quyền dựa trên **Role-Based Access Control**:

| Model            | Mô tả                                      |
|------------------|---------------------------------------------|
| `Role`           | Vai trò (Admin, Nhân sự, Trưởng phòng...) |
| `Module`         | Module chức năng (hr, roles, attendance...) |
| `Permission`     | Hành động trên module (create, read, update, delete) |
| `RolePermission` | Bảng mapping Role ↔ Permission             |

### Cách hoạt động:
- **Backend**: Decorator `@check_permission("module_code", "action")` bảo vệ routes.
- **Frontend**: Hàm `has_permission` được inject vào Jinja context để ẩn/hiện UI elements.
- **Audit**: Mọi thao tác quan trọng được ghi vào bảng `AuditLogs`.

---

## 5. Luồng Duyệt Chấm Công (Approval Flow)

Hệ thống duyệt chấm công 2 cấp:
1. **Cấp 1** - Trưởng phòng duyệt → trạng thái `Pending`
2. **Cấp 2** - Hành chính duyệt → trạng thái `Approved`

Bị từ chối ở bất kỳ cấp nào → trạng thái `Rejected` → Nhân sự có thể sửa và gửi lại.

---

## 6. Kết nối Cơ sở Dữ liệu

```
Driver:   ODBC Driver 18 for SQL Server
Server:   localhost\SQLSERVERTB2
Database: CMMS
Auth:     SQL Server Authentication (UID/PWD)
Options:  Encrypt=yes, TrustServerCertificate=yes, pool_pre_ping=True
```

> **Lưu ý cho AI**: Khi cần sửa connection string, tìm biến `connection_str` trong `app.py`.

---

## 7. Quy ước Code

- **Formatter**: Black (line-length=120)
- **Import order**: Standard Library → Third-party → Local
- **Models**: Đặt trong `models/`, re-export qua `models/__init__.py`
- **Routes**: Mỗi chức năng 1 file Blueprint trong `routes/`
- **Utils**: Hàm tiện ích dùng chung trong `utils/`
