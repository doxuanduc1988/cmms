from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.hr.dependent import HRDependent
from extensions import db
from flask_login import login_required
from utils.permission_utils import check_permission

# Blueprint sử dụng đúng URL theo employee_id
hr_dependent_bp = Blueprint("hr_dependent", __name__, url_prefix="/hr/<employee_id>/dependents")


# Danh sách người phụ thuộc theo nhân viên
@hr_dependent_bp.route("/", methods=["GET"])
@login_required
@check_permission("hr", "read")
def list_dependents(employee_id):
    dependents = HRDependent.query.filter_by(EmployeeID=employee_id).all()
    return render_template("hr/dependents/list.html", dependents=dependents, employee_id=employee_id)


# Thêm người phụ thuộc
@hr_dependent_bp.route("/add", methods=["GET", "POST"])
@login_required
@check_permission("hr", "create")
def add_dependent(employee_id):
    if request.method == "POST":
        try:
            new_dep = HRDependent(
                EmployeeID=employee_id,
                FullName=request.form["FullName"],
                Relationship=request.form["Relationship"],
                BirthDate=request.form.get("BirthDate"),
                Gender=request.form["Gender"],
                Notes=request.form.get("Notes"),
            )
            db.session.add(new_dep)
            db.session.commit()
            flash("Đã thêm người phụ thuộc", "success")
            return redirect(url_for("hr_dependent.list_dependents", employee_id=employee_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi: {str(e)}", "danger")
    return render_template("hr/dependents/form.html", employee_id=employee_id, mode="add")


# Sửa người phụ thuộc
@hr_dependent_bp.route("/edit/<int:dep_id>", methods=["GET", "POST"])
@login_required
@check_permission("hr", "update")
def edit_dependent(employee_id, dep_id):
    dep = HRDependent.query.get_or_404(dep_id)
    if request.method == "POST":
        try:
            dep.FullName = request.form["FullName"]
            dep.Relationship = request.form["Relationship"]
            dep.BirthDate = request.form.get("BirthDate")
            dep.Gender = request.form["Gender"]
            dep.Notes = request.form.get("Notes")
            db.session.commit()
            flash("Đã cập nhật người phụ thuộc", "success")
            return redirect(url_for("hr_dependent.list_dependents", employee_id=employee_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi: {str(e)}", "danger")
    return render_template("hr/dependents/form.html", employee_id=employee_id, dependent=dep, mode="edit")


# Xoá người phụ thuộc
@hr_dependent_bp.route("/delete/<int:dep_id>", methods=["POST"])
@login_required
@check_permission("hr", "delete")
def delete_dependent(employee_id, dep_id):
    dep = HRDependent.query.get(dep_id)
    if dep:
        db.session.delete(dep)
        db.session.commit()
        flash("Đã xoá người phụ thuộc", "success")
    else:
        flash("Không tìm thấy người phụ thuộc", "danger")
    return redirect(url_for("hr_dependent.list_dependents", employee_id=employee_id))
