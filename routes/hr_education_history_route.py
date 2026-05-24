from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models.hr.hr_profiles import HRProfile
from models.hr_education_history import HREducationHistory
from utils.permission_utils import check_permission

education_bp = Blueprint("education", __name__, url_prefix="/hr")


@education_bp.route("/<employee_id>/education")
@check_permission("hr", "read")
def education_list(employee_id):
    employee = HRProfile.query.get_or_404(employee_id)
    records = (
        HREducationHistory.query.filter_by(EmployeeID=employee_id).order_by(HREducationHistory.StartDate.desc()).all()
    )
    return render_template("hr/education_history_list.html", employee=employee, records=records)


@education_bp.route("/<employee_id>/education/create", methods=["GET", "POST"])
@check_permission("hr", "create")
def education_create(employee_id):
    employee = HRProfile.query.get_or_404(employee_id)
    if request.method == "POST":
        record = HREducationHistory(
            EmployeeID=employee_id,
            Degree=request.form.get("Degree"),
            Major=request.form.get("Major"),
            Institution=request.form.get("Institution"),
            StartDate=request.form.get("StartDate"),
            EndDate=request.form.get("EndDate"),
            Form=request.form.get("Form"),
            Notes=request.form.get("Notes"),
        )
        db.session.add(record)
        db.session.commit()
        flash("Đã thêm quá trình học tập", "success")
        return redirect(url_for("education.education_list", employee_id=employee_id))
    return render_template("hr/education_history_form.html", employee=employee, action="create")


@education_bp.route("/<employee_id>/education/<int:edu_id>/edit", methods=["GET", "POST"])
@check_permission("hr", "update")
def education_edit(employee_id, edu_id):
    employee = HRProfile.query.get_or_404(employee_id)
    record = HREducationHistory.query.get_or_404(edu_id)
    if request.method == "POST":
        record.Degree = request.form.get("Degree")
        record.Major = request.form.get("Major")
        record.Institution = request.form.get("Institution")
        record.StartDate = request.form.get("StartDate")
        record.EndDate = request.form.get("EndDate")
        record.Form = request.form.get("Form")
        record.Notes = request.form.get("Notes")
        db.session.commit()
        flash("Đã cập nhật quá trình học tập", "success")
        return redirect(url_for("education.education_list", employee_id=employee_id))
    return render_template("hr/education_history_form.html", employee=employee, record=record, action="edit")


@education_bp.route("/<employee_id>/education/<int:edu_id>/delete", methods=["POST"])
@check_permission("hr", "delete")
def education_delete(employee_id, edu_id):
    record = HREducationHistory.query.get_or_404(edu_id)
    db.session.delete(record)
    db.session.commit()
    flash("Đã xoá quá trình học tập", "info")
    return redirect(url_for("education.education_list", employee_id=employee_id))
