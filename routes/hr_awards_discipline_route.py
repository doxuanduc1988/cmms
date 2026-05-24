from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models.hr.hr_profiles import HRProfile
from models.hr_awards_discipline_model import HRAwardsDiscipline
from utils.permission_utils import check_permission

award_discipline_bp = Blueprint("award_discipline", __name__, url_prefix="/hr")


@award_discipline_bp.route("/<employee_id>/awards")
@check_permission("hr", "read")
def list_awards(employee_id):
    employee = HRProfile.query.get_or_404(employee_id)
    records = HRAwardsDiscipline.query.filter_by(EmployeeID=employee_id).order_by(HRAwardsDiscipline.Date.desc()).all()
    return render_template("hr/award_discipline_list.html", employee=employee, records=records)


@award_discipline_bp.route("/<employee_id>/awards/create", methods=["GET", "POST"])
@check_permission("hr", "create")
def create_award(employee_id):
    employee = HRProfile.query.get_or_404(employee_id)
    if request.method == "POST":
        record = HRAwardsDiscipline(
            EmployeeID=employee_id,
            Type=request.form.get("Type"),
            Title=request.form.get("Title"),
            Date=request.form.get("Date"),
            DecisionNumber=request.form.get("DecisionNumber"),
            Notes=request.form.get("Notes"),
        )
        db.session.add(record)
        db.session.commit()
        flash("Đã thêm khen thưởng/kỷ luật.", "success")
        return redirect(url_for("award_discipline.list_awards", employee_id=employee_id))
    return render_template("hr/award_discipline_form.html", employee=employee, action="create")


@award_discipline_bp.route("/<employee_id>/awards/<int:record_id>/edit", methods=["GET", "POST"])
@check_permission("hr", "update")
def edit_award(employee_id, record_id):
    employee = HRProfile.query.get_or_404(employee_id)
    record = HRAwardsDiscipline.query.get_or_404(record_id)
    if request.method == "POST":
        record.Type = request.form.get("Type")
        record.Title = request.form.get("Title")
        record.Date = request.form.get("Date")
        record.DecisionNumber = request.form.get("DecisionNumber")
        record.Notes = request.form.get("Notes")
        db.session.commit()
        flash("Đã cập nhật bản ghi.", "success")
        return redirect(url_for("award_discipline.list_awards", employee_id=employee_id))
    return render_template("hr/award_discipline_form.html", employee=employee, record=record, action="edit")


@award_discipline_bp.route("/<employee_id>/awards/<int:record_id>/delete", methods=["POST"])
@check_permission("hr", "delete")
def delete_award(employee_id, record_id):
    record = HRAwardsDiscipline.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash("Đã xoá bản ghi.", "info")
    return redirect(url_for("award_discipline.list_awards", employee_id=employee_id))
