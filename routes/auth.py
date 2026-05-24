# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import session

from flask_login import login_user, logout_user, login_required
from models.hr.employee_model import Employee
from extensions import db
from utils.password_utils import hash_password, check_password  # ✅ dùng bcrypt
from utils.permission_utils import refresh_session_permissions, clear_session_permissions

# from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = Employee.query.filter_by(Username=username).first()

        if not user:
            flash("❌ Sai tên đăng nhập", "danger")
        elif user.Status.lower() != "active":
            flash("⚠️ Tài khoản không hoạt động", "warning")
        elif not check_password(password, user.PasswordHash):

            flash("❌ Mật khẩu không đúng", "danger")
        else:
            login_user(user)
            session["employee_id"] = user.EmployeeID
            session["full_name"] = user.FullName or user.Username or "Chưa cập nhật"
            session["department_code"] = user.DepartmentCode
            refresh_session_permissions(user)

            return redirect(url_for("dashboard.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    clear_session_permissions()
    session.clear()
    logout_user()
    flash("🚪 Đã đăng xuất", "info")
    return redirect(url_for("auth.login"))
