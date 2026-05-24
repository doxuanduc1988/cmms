# routes/hr_leave_route.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models.hr.hr_profiles import HRProfile
from models.hr_leave import HRLeaveRequest
from utils.permission_utils import check_permission
from datetime import datetime

leave_bp = Blueprint("leave", __name__, url_prefix="/hr")


@leave_bp.route("/<employee_id>/leave")
@check_permission("hr", "read")
def list_leave(employee_id):
    employee = HRProfile.query.get_or_404(employee_id)
    records = HRLeaveRequest.query.filter_by(EmployeeID=employee_id).order_by(HRLeaveRequest.StartDate.desc()).all()
    return render_template("hr/leave_list.html", employee=employee, records=records)


@leave_bp.route("/<employee_id>/leave/create", methods=["GET", "POST"])
@check_permission("hr", "create")
def create_leave(employee_id):
    employee = HRProfile.query.get_or_404(employee_id)
    if request.method == "POST":
        record = HRLeaveRequest(
            EmployeeID=employee_id,
            LeaveType=request.form["LeaveType"],
            StartDate=request.form["StartDate"],
            EndDate=request.form["EndDate"],
            TotalDays=request.form["TotalDays"],
            OTReference=request.form.get("OTReference"),
            Reason=request.form.get("Reason"),
            Status=request.form["Status"],
            Notes=request.form.get("Notes"),
        )
        db.session.add(record)
        db.session.commit()
        flash("Đã thêm đơn nghỉ", "success")
        return redirect(url_for("leave.list_leave", employee_id=employee_id))
    return render_template("hr/leave_form.html", employee=employee, action="create")


@leave_bp.route("/<employee_id>/leave/<int:leave_id>/edit", methods=["GET", "POST"])
@check_permission("hr", "update")
def edit_leave(employee_id, leave_id):
    employee = HRProfile.query.get_or_404(employee_id)
    record = HRLeaveRequest.query.get_or_404(leave_id)
    if request.method == "POST":
        record.LeaveType = request.form["LeaveType"]
        record.StartDate = request.form["StartDate"]
        record.EndDate = request.form["EndDate"]
        record.TotalDays = request.form["TotalDays"]
        record.OTReference = request.form.get("OTReference")
        record.Reason = request.form.get("Reason")
        record.Status = request.form["Status"]
        record.Notes = request.form.get("Notes")
        db.session.commit()
        flash("Đã cập nhật đơn nghỉ", "success")
        return redirect(url_for("leave.list_leave", employee_id=employee_id))
    return render_template("hr/leave_form.html", employee=employee, record=record, action="edit")


@leave_bp.route("/<employee_id>/leave/<int:leave_id>/delete", methods=["POST"])
@check_permission("hr", "delete")
def delete_leave(employee_id, leave_id):
    record = HRLeaveRequest.query.get_or_404(leave_id)
    db.session.delete(record)
    db.session.commit()
    flash("Đã xoá đơn nghỉ.", "info")
    return redirect(url_for("leave.list_leave", employee_id=employee_id))
