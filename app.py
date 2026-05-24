# ===== app.py =====
# File khởi tạo chính của ứng dụng Flask CMMS.
# Cấu hình DB, Login Manager, đăng ký Blueprints.

# ---------- Standard Library ----------
import os
import sys
from importlib.metadata import version
from urllib.parse import quote_plus

# ---------- Third-party ----------
import flask
from flask import Flask, render_template, redirect
from flask_login import LoginManager, login_required
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

# ---------- Local: Extensions ----------
from extensions import db

# ---------- Local: Utils ----------
from utils.permission_utils import has_permission, has_permission_view

# ---------- Local: Config ----------
from config import ENFORCE_DATE_LOCK, UPLOAD_FOLDER_HEALTH

# ---------- Local: Models (dùng trong file này) ----------
from models.hr.employee_model import Employee

# =============================================================================
# BLUEPRINT IMPORTS
# Tổ chức theo nhóm chức năng, mỗi nhóm ghi chú rõ ràng.
# =============================================================================

# --- Auth & Account ---
from routes.auth import auth_bp
from routes.account import account_bp

# --- Dashboard ---
from routes.dashboard import dashboard_bp

# --- Nhân sự (HR) ---
from routes.employees import employee_bp
from routes.hr import hr_bp
from routes.hr_work_history import work_history_bp
from routes.hr_salary_history import salary_history_bp
from routes.hr_salary_table_route import salary_table_bp
from routes.hr_education_history_route import education_bp
from routes.hr_awards_discipline_route import award_discipline_bp
from routes.hr_contract_route import contract_bp
from routes.hr_leave_route import leave_bp
from routes.hr_health_route import hr_health_bp
from routes.health_index_route import health_index_bp
from routes.dependent_route import hr_dependent_bp
from routes.report_resume import hr_report_resume_bp
from routes.report_route import hr_report_bp

# --- Phòng ban / Vị trí ---
from routes.departments import department_bp
from routes.job_positions import job_position_bp

# --- Phân quyền ---
from routes.roles import role_bp
from routes.permissions import permission_bp
from routes.permission_manage_route import permission_manage_bp

# --- Audit ---
from routes.audit import audit_bp

# --- Tổ / Ca / Phân công ---
from routes.crew_route import crew_bp
from routes.crew_assignments import crew_assignment_bp
from routes.crew_assign_assign_route import assign_bp
from routes.crew_definitions.crew_definitions_route import crew_definitions_bp

# --- Chấm công (Attendance) ---
from routes.attendance.attendance_bulk_create_full_v2 import attendance_bulk_bp
from routes.attendance.attendance_check_route import attendance_check_bp
from routes.attendance.attendance_edit_route import attendance_edit_bp
from routes.attendance.attendance_log_route import attendance_log_bp
from routes.attendance.attendance_unmarked_route import attendance_unmarked_bp
from routes.attendance.attendance_create_route import attendance_create_bp
from routes.attendance.attendance_monthly_summary_route import attendance_summary_bp
from routes.attendance.attendance_export_excel_route import attendance_export_bp
from routes.attendance.attendance_approval_route import attendance_approval_bp
from routes.attendance.attendance_approval_dashboard_route import attendance_dashboard_bp
from routes.attendance.attendance_rejected_route import attendance_rejected_bp
from routes.attendance.attendance_grid_route import attendance_grid_bp

# --- Thống kê chấm công ---
from routes.attendance.stats.attendance_stats_by_dept import attendance_stats_bp
from routes.attendance.stats.attendance_pie_stats_route import attendance_pie_bp
from routes.attendance.stats.attendance_avg_by_shift_route import attendance_avg_shift_bp
from routes.attendance.stats.attendance_dashboard_route import stats_dashboard_bp

# --- Báo cáo chấm công ---
from routes.attendance.report_attendance_excel_route import report_bp

# --- Mua sắm ---
from routes.procurement import procurement_bp

# --- Dự toán ---
from routes.estimation import estimation_bp

# =============================================================================
# KHỞI TẠO ỨNG DỤNG
# =============================================================================

app = Flask(__name__)
app.secret_key = "your-secret-key"

# --- Login Manager ---
login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Bạn cần đăng nhập để tiếp tục."
login_manager.login_message_category = "error"


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(Employee, str(user_id))


# --- Database Connection ---
db_type = os.environ.get("DB_TYPE", "mssql").lower()

if db_type == "mysql" or db_type == "mariadb":
    # MariaDB / MySQL Connection
    db_server = os.environ.get("DB_SERVER", "mariadb")
    db_name = os.environ.get("DB_NAME", "CMMS")
    db_user = os.environ.get("DB_USER", "cmms_user")
    db_password = os.environ.get("DB_PASSWORD", "cmms@Admin123")
    encoded_password = quote_plus(db_password)
    
    # Sử dụng mysqlclient (mysql://) hoặc pymysql
    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql://{db_user}:{encoded_password}@{db_server}/{db_name}?charset=utf8mb4"
else:
    # SQL Server (MSSQL) Connection
    db_server = os.environ.get("DB_SERVER", "localhost\\SQLSERVERTB2")
    db_name = os.environ.get("DB_NAME", "CMMS")
    db_user = os.environ.get("DB_USER", "newsa")
    db_password = os.environ.get("DB_PASSWORD", "cmms123")
    driver = "ODBC Driver 18 for SQL Server"

    connection_str = (
        f"DRIVER={driver};"
        f"SERVER={db_server};"
        f"DATABASE={db_name};"
        f"UID={db_user};"
        f"PWD={db_password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )
    params = quote_plus(connection_str)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"mssql+pyodbc:///?odbc_connect={params}"

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

# --- Khởi tạo SQLAlchemy ---
db.init_app(app)


# =============================================================================
# ĐĂNG KÝ BLUEPRINTS
# Dùng danh sách để dễ quản lý khi thêm/bớt module trong tương lai.
# =============================================================================

_blueprints = [
    # Auth & Account
    auth_bp,
    account_bp,
    # Dashboard
    dashboard_bp,
    # Nhân sự (HR)
    employee_bp,
    hr_bp,
    work_history_bp,
    salary_history_bp,
    salary_table_bp,
    education_bp,
    award_discipline_bp,
    contract_bp,
    leave_bp,
    hr_health_bp,
    health_index_bp,
    hr_dependent_bp,
    hr_report_resume_bp,
    hr_report_bp,
    # Phòng ban / Vị trí
    department_bp,
    job_position_bp,
    # Phân quyền
    role_bp,
    permission_bp,
    permission_manage_bp,
    # Audit
    audit_bp,
    # Tổ / Ca / Phân công
    crew_bp,
    crew_assignment_bp,
    assign_bp,
    crew_definitions_bp,
    # Chấm công
    attendance_bulk_bp,
    attendance_check_bp,
    attendance_edit_bp,
    attendance_log_bp,
    attendance_unmarked_bp,
    attendance_create_bp,
    attendance_summary_bp,
    attendance_export_bp,
    attendance_approval_bp,
    attendance_dashboard_bp,
    attendance_rejected_bp,
    attendance_grid_bp,
    # Thống kê chấm công
    attendance_stats_bp,
    attendance_pie_bp,
    attendance_avg_shift_bp,
    stats_dashboard_bp,
    # Báo cáo
    report_bp,
    # Mua sắm
    procurement_bp,
    # Dự toán
    estimation_bp,
]

for bp in _blueprints:
    app.register_blueprint(bp)


# =============================================================================
# JINJA GLOBALS & CONTEXT PROCESSOR
# =============================================================================

app.jinja_env.globals["has_permission"] = has_permission


@app.context_processor
def inject_permissions():
    return dict(has_permission=has_permission_view)


# =============================================================================
# KIỂM TRA KẾT NỐI DB (chỉ 1 lần duy nhất)
# =============================================================================


@app.before_request
def check_db_connection_once():
    if not hasattr(app, "_db_checked"):
        try:
            db.session.execute(text("SELECT 1"))
            print("✅ Kết nối DB OK")
        except Exception as e:
            print("❌ Lỗi kết nối DB:", e)
        app._db_checked = True


# =============================================================================
# GLOBAL ERROR HANDLERS
# Xử lý ngoại lệ toàn cục để tránh hiển thị trang lỗi 500 khi người dùng
# vi phạm khóa ngoại (vd: xóa dữ liệu đang được sử dụng) hoặc lỗi hệ thống.
# =============================================================================
from sqlalchemy.exc import IntegrityError
from flask import request, flash, url_for, redirect

@app.errorhandler(IntegrityError)
def handle_integrity_error(e):
    db.session.rollback()
    # Thông báo lịch sự thay vì 500 Error
    flash("⚠️ Không thể thực hiện! Dữ liệu đang được sử dụng hoặc thao tác không hợp lệ.", "danger")
    return redirect(request.referrer or url_for("dashboard"))

@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    # Trong trường hợp người dùng cố tình thao tác không có quyền hoặc lỗi code
    return redirect(request.referrer or url_for("dashboard"))

@app.errorhandler(403)
def forbidden_error(e):
    return redirect(request.referrer or url_for("dashboard"))

# =============================================================================
# ROUTES CHÍNH
# =============================================================================


@app.route("/")
def home():
    return redirect("/dashboard")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/dashboard/accounts")
@login_required
def dashboard_accounts():
    return render_template("accounts_dashboard.html")


@app.route("/dashboard/hr")
@login_required
def dashboard_hr():
    return render_template("hr_dashboard.html")


@app.route("/dashboard/attendance")
@login_required
def dashboard_attendance():
    return redirect("/attendance/stats/dashboard")


# =============================================================================
# ENTRYPOINT
# =============================================================================

if __name__ == "__main__":
    try:
        print("✅ Flask version:", version("flask"))
    except Exception:
        print("✅ Flask version: unknown")

    print("✅ Flask loaded from:", flask.__file__)

    with app.app_context():
        print(">>> URL MAP (after blueprints):")
        for r in app.url_map.iter_rules():
            print(f"{r.endpoint} -> {r}")

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
