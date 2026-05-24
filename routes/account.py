# ===== routes/accounts.py =====
import random
import string
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from extensions import db
from models.audit_logs import AuditLog
from models.hr.employee_model import Employee
from models.roles import Role
from utils.password_utils import check_password, hash_password
from utils.permission_utils import check_permission
from utils.role_catalog import get_assignable_roles, resolve_role_ids_to_canonical

account_bp = Blueprint("account", __name__, url_prefix="/accounts")


def generate_temp_password(length=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


@account_bp.route("/")
@login_required
@check_permission("system_admin", "read")
def list_accounts():
    employees = Employee.query.all()
    return render_template("accounts/list.html", employees=employees)


@account_bp.route("/create", methods=["GET", "POST"])
@login_required
@check_permission("system_admin", "create")
def create_account():
    roles = get_assignable_roles()
    if request.method == "POST":
        new_emp = Employee(
            EmployeeID=request.form["EmployeeID"],
            FullName=request.form["FullName"],
            Username=request.form["Username"],
            PasswordHash=hash_password(request.form["Password"]),
            Status=request.form.get("Status", "active"),
            Email=request.form.get("Email"),
            Phone=request.form.get("Phone"),
        )
        role_ids = request.form.getlist("RoleIDs")
        if role_ids:
            new_emp.roles = resolve_role_ids_to_canonical(role_ids)
        db.session.add(new_emp)
        db.session.commit()
        flash("✅ Đã tạo tài khoản mới", "success")
        return redirect(url_for("account.list_accounts"))
    return render_template("accounts/create.html", roles=roles)


@account_bp.route("/change_password/<EmployeeID>", methods=["GET", "POST"])
@login_required
@check_permission("system_admin", "update")
def change_password(EmployeeID):
    emp = Employee.query.get_or_404(EmployeeID)
    if request.method == "POST":
        new_password = request.form["Password"]
        emp.PasswordHash = hash_password(new_password)
        db.session.commit()
        flash("🔐 Đã đổi mật khẩu", "success")
        return redirect(url_for("account.list_accounts"))
    return render_template("accounts/change_password.html", emp=emp)


@account_bp.route("/change-own-password", methods=["GET", "POST"])
@login_required
def change_own_password():
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            flash("❌ Mật khẩu mới và xác nhận không khớp.", "danger")
            return redirect(url_for("account.change_own_password"))

        user = current_user

        if not user.PasswordHash or not user.PasswordHash.strip():
            flash(
                "❌ Tài khoản hiện tại chưa có mật khẩu. Vui lòng liên hệ quản trị viên để đặt lại mật khẩu.",
                "danger",
            )
            return redirect(url_for("account.change_own_password"))

        if not check_password(current_password, user.PasswordHash):
            flash("❌ Mật khẩu hiện tại không hợp lệ. Vui lòng liên hệ quản trị viên.", "danger")
            return redirect(url_for("account.change_own_password"))

        user.PasswordHash = hash_password(new_password)
        db.session.commit()

        flash("✅ Đổi mật khẩu thành công!", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("accounts/change_own_password.html")


@account_bp.route("/reset_password/<EmployeeID>", methods=["POST"])
@login_required
@check_permission("system_admin", "update")
def reset_password(EmployeeID):
    emp = Employee.query.get_or_404(EmployeeID)
    new_password = generate_temp_password()
    emp.PasswordHash = hash_password(new_password)
    db.session.commit()

    log = AuditLog(
        EmployeeID=current_user.EmployeeID,
        Module="Accounts",
        Action="Reset Password",
        Description=f"{current_user.Username} reset mật khẩu cho {emp.Username} ({emp.EmployeeID})",
    )
    db.session.add(log)
    db.session.commit()

    flash(f"✅ Mật khẩu mới của {emp.FullName} là: {new_password}", "info")
    return redirect(url_for("account.list_accounts"))
