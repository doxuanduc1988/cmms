# routes/employees.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user  # ✅ thêm current_user
from models.hr.employee_model import Employee
from models.roles import Role
from models.hr.department_model import Department
from extensions import db
from utils.permission_utils import check_permission
from utils.audit_utils import log_action
from utils.password_utils import hash_password  # dùng cùng cơ chế login
from utils.role_catalog import get_assignable_roles, resolve_role_ids_to_canonical

employee_bp = Blueprint("employee", __name__, url_prefix="/employees")


# Danh sách nhân viên với phân trang
@employee_bp.route("/")
@login_required
@check_permission("system_admin", "read")
def list_employees():
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 10

    query = Employee.query
    if search:
        query = query.filter(Employee.FullName.ilike(f"%{search}%"))

    employees = query.order_by(Employee.FullName.asc()).paginate(page=page, per_page=per_page)
    return render_template("employees/list.html", employees=employees, search=search)


# Tạo mới tài khoản
@employee_bp.route("/create", methods=["GET", "POST"])
@login_required
@check_permission("system_admin", "create")
def create_employee():
    if request.method == "POST":
        emp_id = request.form["EmployeeID"]
        username = request.form["Username"]
        password = request.form["Password"]

        if Employee.query.filter_by(EmployeeID=emp_id).first():
            flash("Mã nhân viên đã tồn tại", "danger")
            return redirect(url_for("employee.create_employee"))

        new_emp = Employee(
            EmployeeID=emp_id,
            FullName=request.form.get("FullName"),
            Username=username,
            PasswordHash=hash_password(password),
            DepartmentCode=request.form.get("DepartmentCode"),
            Status=request.form.get("Status") or "Active",
        )

        # ✅ Gán nhiều vai trò
        role_ids = request.form.getlist("RoleIDs")
        if role_ids:
            new_emp.roles = resolve_role_ids_to_canonical(role_ids)

        db.session.add(new_emp)
        db.session.commit()
        # ghi log sau commit (không ảnh hưởng dữ liệu chính)
        try:
            log_action(current_user.EmployeeID, "create", "employees", f"Tạo tài khoản nhân viên: {emp_id}")
        except Exception:
            # Bỏ qua nếu lỗi ghi log để không làm hỏng tiến trình tạo tài khoản
            pass

        flash("Đã tạo tài khoản mới", "success")
        return redirect(url_for("employee.list_employees"))

    roles = get_assignable_roles()
    departments = Department.query.all()
    return render_template("employees/create.html", roles=roles, departments=departments)


# Chỉnh sửa tài khoản
@employee_bp.route("/edit/<string:employee_id>", methods=["GET", "POST"])
@login_required
@check_permission("system_admin", "update")
def edit_employee(employee_id):
    emp = Employee.query.get_or_404(employee_id)

    if request.method == "POST":
        emp.FullName = request.form.get("FullName")
        emp.DepartmentCode = request.form.get("DepartmentCode")
        emp.Status = request.form.get("Status")

        # ✅ Cập nhật nhiều vai trò
        role_ids = request.form.getlist("RoleIDs")
        emp.roles = resolve_role_ids_to_canonical(role_ids)

        db.session.commit()
        flash("Đã cập nhật thông tin nhân viên", "success")
        return redirect(url_for("employee.list_employees"))

    roles = get_assignable_roles()
    departments = Department.query.all()
    canonical = resolve_role_ids_to_canonical([r.RoleID for r in emp.roles])
    emp_canonical_role_ids = [r.RoleID for r in canonical]
    return render_template(
        "employees/edit.html",
        emp=emp,
        roles=roles,
        departments=departments,
        emp_canonical_role_ids=emp_canonical_role_ids,
    )


# Xoá nhân viên
@employee_bp.route("/delete/<string:employee_id>", methods=["POST"])
@login_required
@check_permission("system_admin", "delete")
def delete_employee(employee_id):
    emp = Employee.query.get_or_404(employee_id)
    db.session.delete(emp)
    db.session.commit()
    flash("🗑️ Đã xoá tài khoản nhân viên", "success")
    return redirect(url_for("employee.list_employees"))


# ✅ Reset mật khẩu nhân viên (GIỮ NGUYÊN GIAO DIỆN)
@employee_bp.route("/reset-password/<string:employee_id>", methods=["POST"])
@login_required
@check_permission("system_admin", "update")
def reset_password(employee_id):
    """
    - Nhận mật khẩu mới từ input hidden name="NewPassword" (UI hiện có).
    - Nếu thiếu -> fallback '123456' (khớp giao diện).
    - Hash, commit, flash hiển thị mật khẩu mới.
    - Ghi log hành động (không rollback dữ liệu nếu log lỗi).
    """
    emp = Employee.query.get_or_404(employee_id)

    # Lấy mật khẩu mới theo đúng tên trường trong template
    new_password = (request.form.get("NewPassword") or "").strip()
    if not new_password:
        new_password = "123456"  # fallback để nút reset luôn hoạt động

    try:
        # Băm và lưu
        emp.PasswordHash = hash_password(new_password)
        db.session.commit()

        # Ghi log (không ảnh hưởng kết quả reset)
        try:
            actor = getattr(current_user, "Username", "system")
            actor_id = getattr(current_user, "EmployeeID", "system")
            log_action(
                actor_id,
                "reset_password",
                "employees",
                f"{actor} reset mật khẩu cho {emp.Username} ({emp.EmployeeID})",
            )
        except Exception:
            pass

        # Thông báo ra UI (list.html đã có block get_flashed_messages)
        flash(f"✅ Đã đặt lại mật khẩu cho {emp.FullName}: {new_password}", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Lỗi khi đặt lại mật khẩu: {e}", "danger")

    return redirect(url_for("employee.list_employees"))
