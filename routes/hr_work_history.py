from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models.hr_work_history import HRWorkHistory
from models.hr.hr_profiles import HRProfile
from models.hr.department_model import Department
from utils.permission_utils import check_permission

work_history_bp = Blueprint("work_history", __name__, url_prefix="/hr")


@work_history_bp.route("/<employee_id>/work-history")
@check_permission("hr", "read")
def work_history_list(employee_id):
    employee = HRProfile.query.get_or_404(employee_id)
    history = HRWorkHistory.query.filter_by(EmployeeID=employee_id).order_by(HRWorkHistory.StartDate.desc()).all()
    return render_template("hr/work_history_list.html", employee=employee, history=history)


@work_history_bp.route("/<employee_id>/work-history/create", methods=["GET", "POST"])
@check_permission("hr", "create")
def work_history_create(employee_id):
    employee = HRProfile.query.get_or_404(employee_id)
    departments = Department.query.all()

    if request.method == "POST":
        new_record = HRWorkHistory(
            EmployeeID=employee_id,
            StartDate=request.form["StartDate"],
            ToDate=request.form.get("ToDate") or None,
            DepartmentName=request.form.get("DepartmentName") or None,
            Position=request.form.get("Position"),
            Notes=request.form.get("Notes"),
        )
        db.session.add(new_record)
        db.session.commit()
        flash("Đã thêm quá trình công tác.", "success")
        return redirect(url_for("work_history.work_history_list", employee_id=employee_id))

    return render_template("hr/work_history_form.html", employee=employee, departments=departments, action="create")


@work_history_bp.route("/<employee_id>/work-history/<int:work_id>/edit", methods=["GET", "POST"])
@check_permission("hr", "update")
def work_history_edit(employee_id, work_id):
    record = HRWorkHistory.query.get_or_404(work_id)
    employee = HRProfile.query.get_or_404(employee_id)
    departments = Department.query.all()

    if request.method == "POST":
        record.StartDate = request.form["StartDate"]
        record.ToDate = request.form.get("ToDate") or None
        record.DepartmentName = request.form.get("DepartmentName") or None
        record.Position = request.form.get("Position")
        record.Notes = request.form.get("Notes")
        db.session.commit()
        flash("Đã cập nhật quá trình công tác.", "success")
        return redirect(url_for("work_history.work_history_list", employee_id=employee_id))

    return render_template(
        "hr/work_history_form.html", employee=employee, record=record, departments=departments, action="edit"
    )


@work_history_bp.route("/<employee_id>/work-history/<int:work_id>/delete", methods=["POST"])
@check_permission("hr", "delete")
def work_history_delete(employee_id, work_id):
    record = HRWorkHistory.query.get_or_404(work_id)
    db.session.delete(record)
    db.session.commit()
    flash("Đã xoá quá trình công tác.", "info")
    return redirect(url_for("work_history.work_history_list", employee_id=employee_id))
