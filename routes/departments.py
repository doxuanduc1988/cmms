from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models.hr.department_model import Department


from utils.permission_utils import has_permission
from flask_login import login_required
from utils.decorators import role_required  # nếu bạn có custom

from utils.permission_utils import check_permission


from sqlalchemy import text

department_bp = Blueprint("department", __name__, url_prefix="/departments")


# 🔹 Danh sách phòng ban
@department_bp.route("/", methods=["GET"])
@login_required
@check_permission("department", "read")   # ✅ kiểm tra quyền xem
def list_departments():
    departments = Department.query.all()
    return render_template("departments/list.html", departments=departments)


# 🔹 Thêm mới phòng ban
@department_bp.route("/create", methods=["GET", "POST"])
@login_required
@check_permission("department", "create")  # ✅ kiểm tra quyền thêm
def create_department():

    if request.method == "POST":
        department_code = request.form["DepartmentCode"]

        # Kiểm tra mã phòng ban đã tồn tại chưa
        if Department.query.get(department_code):
            flash("❌ Mã phòng ban đã tồn tại!", "error")
            return render_template("departments/create.html")

        try:
            new_department = Department(
                DepartmentCode=department_code,
                DepartmentName=request.form["DepartmentName"],
                Description=request.form["Description"],
            )
            db.session.add(new_department)
            db.session.commit()
            flash("✅ Đã thêm phòng ban mới!", "success")
            return redirect(url_for("department.list_departments"))
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Lỗi khi thêm phòng ban: {e}", "error")

    return render_template("departments/create.html")


# 🔹 Chỉnh sửa phòng ban
@department_bp.route("/edit/<DepartmentCode>", methods=["GET", "POST"])
@login_required
@check_permission("department", "update")  # ✅ kiểm tra quyền sửa
def edit_department(DepartmentCode):
    department = Department.query.get_or_404(DepartmentCode)

    if request.method == "POST":
        try:
            department.DepartmentName = request.form["DepartmentName"]
            department.Description = request.form["Description"]
            db.session.commit()
            flash("✅ Đã cập nhật thông tin phòng ban!", "success")
            return redirect(url_for("department.list_departments"))
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Lỗi khi cập nhật phòng ban: {e}", "error")

    return render_template("departments/edit.html", department=department)


# 🔹 Xoá phòng ban
@department_bp.route("/delete/<DepartmentCode>", methods=["POST"])
@login_required
@check_permission("department", "delete")  # ✅ kiểm tra quyền xoá
def delete_department(DepartmentCode):

    department = Department.query.get_or_404(DepartmentCode)

    try:
        db.session.delete(department)
        db.session.commit()
        flash("🗑️ Đã xoá phòng ban!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Lỗi khi xoá phòng ban: {e}", "error")

    return redirect(url_for("department.list_departments"))
