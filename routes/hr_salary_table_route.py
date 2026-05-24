from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models.hr_salary_table import HRSalaryTable
from utils.permission_utils import check_permission

salary_table_bp = Blueprint("salary_table", __name__, url_prefix="/salary-table")


@salary_table_bp.route("/")
@check_permission("hr_salary", "read")
def salary_table_list():
    salary_table = HRSalaryTable.query.order_by(HRSalaryTable.SalaryCode).all()
    return render_template("hr/salary_table_list.html", salary_table=salary_table)


@salary_table_bp.route("/create", methods=["GET", "POST"])
@check_permission("hr_salary", "create")
def salary_table_create():
    if request.method == "POST":
        new_item = HRSalaryTable(
            SalaryCode=request.form["SalaryCode"],
            Description=request.form.get("Description"),
            Coefficient=request.form.get("Coefficient") or 0,
        )
        db.session.add(new_item)
        db.session.commit()
        flash("Đã thêm bậc lương.", "success")
        return redirect(url_for("salary_table.salary_table_list"))
    return render_template("hr/salary_table_form.html", action="create", record=None)


@salary_table_bp.route("/<code>/edit", methods=["GET", "POST"])
@check_permission("hr_salary", "update")
def salary_table_edit(code):
    record = HRSalaryTable.query.get_or_404(code)
    if request.method == "POST":
        record.Description = request.form.get("Description")
        record.Coefficient = request.form.get("Coefficient") or 0
        db.session.commit()
        flash("Đã cập nhật bậc lương.", "success")
        return redirect(url_for("salary_table.salary_table_list"))
    return render_template("hr/salary_table_form.html", action="edit", record=record)


@salary_table_bp.route("/<code>/delete", methods=["POST"])
@check_permission("hr_salary", "delete")
def salary_table_delete(code):
    record = HRSalaryTable.query.get_or_404(code)
    db.session.delete(record)
    db.session.commit()
    flash("Đã xoá bậc lương.", "info")
    return redirect(url_for("salary_table.salary_table_list"))
