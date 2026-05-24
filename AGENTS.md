# CMMS TB2 — Hướng dẫn cho AI / Developer

Hệ thống quản trị Nhà máy Nhiệt điện Thái Bình 2: **Flask monolith** + **MariaDB/SQL Server** + Jinja2.

## Chạy lệnh Python (bắt buộc dùng virtualenv)

`python3` hệ thống **không** có Flask. Luôn kích hoạt venv trước:

```bash
cd ~/cmms

# Ubuntu: nếu lỗi ensurepip, cài trước: sudo apt install python3-venv python3-pip

# Tạo venv lần đầu (chỉ một lần)
python3 -m venv myvenv

# Kích hoạt (mỗi phiên terminal)
source myvenv/bin/activate   # Linux/macOS
# myvenv\Scripts\activate    # Windows

pip install -r requirements.txt

# Script bảo trì RBAC
python fix_permissions.py
python setup_rbac.py
```

Hoặc một dòng:

```bash
./scripts/run_in_venv.sh python setup_rbac.py
```

**Docker:** app chạy trong container đã cài dependencies — RBAC trên host DB:

```bash
docker compose exec web python setup_rbac.py
```

## Cấu trúc thư mục

| Path | Vai trò |
|------|---------|
| `app.py` | Factory Flask, đăng ký blueprints, DB URI |
| `run.py` | WSGI entry (Gunicorn) |
| `routes/` | Blueprint theo phân hệ |
| `models/` | SQLAlchemy (canonical — **không** dùng `models.py` gốc) |
| `utils/permission_utils.py` | RBAC 3 lớp: access, CRUD, data scope |
| `setup_rbac.py` | Đồng bộ modules + vai trò mẫu |
| `templates/` | Jinja2 UI |
| `system.md` | Kiến trúc chi tiết |

## Phân hệ & ModuleCode RBAC

| Phân hệ | `ModuleCode` |
|---------|----------------|
| Quản trị | `system_admin` |
| Nhân sự | `hr` |
| Lương | `hr_salary` |
| Sức khỏe | `hr_health` |
| Phòng ban | `department` |
| Chấm công | `attendance` |
| Ca/tổ | `crew` |
| Mua sắm | `procurement` |
| Dự toán | `estimation` |

Actions: `access`, `read`, `create`, `update`, `delete`.

- Decorator route: `@check_permission("hr", "read")`
- Template: `has_module_access('hr')`, `has_permission('hr', 'update')`
- Sau login: `refresh_session_permissions(user)` cache vào session.

Vai trò mẫu (setup_rbac): `admin`, `nhansu`, `hanhchinh`, `truongphong`, `muasam`, `du_toan`, `lanhdao`, `canbo`.

## Tag rollback

`v1.0-stable` — snapshot trước RBAC mới: `git checkout v1.0-stable`

## Không commit

- `logs/`, `uploads/`, `myvenv/`, `.env`, `*.bak`, `*.sql`
- File test/scratch đã xóa khỏi repo

## Ghi chú triển khai

- Ubuntu + Docker: xem `DEPLOYMENT_UBUNTU.md`
- Windows + SQL Server: xem `setup_instructions.md`
