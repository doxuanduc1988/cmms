from flask import Blueprint, render_template, session, abort, request, redirect, url_for, flash
from extensions import db
from models.attendance.attendance_model import Attendance
from models.attendance.approval_status import AttendanceApprovalStatus
from models.attendance.approval_flow import AttendanceApprovalFlow
from models.hr.employee_model import Employee
import copy
from utils.attendance_log_utils import log_attendance_change_from_objects
from flask_login import login_required
from utils.permission_utils import check_permission

attendance_rejected_bp = Blueprint("attendance_rejected", __name__)


@attendance_rejected_bp.route("/attendance/rejected")
@login_required
@check_permission("attendance", "update")
def list_rejected_attendance():
    subquery = (
        db.session.query(
            AttendanceApprovalFlow.AttendanceID,
            AttendanceApprovalFlow.ApprovedBy,
            AttendanceApprovalFlow.ApprovedAt,
            AttendanceApprovalFlow.Note,
        )
        .filter(AttendanceApprovalFlow.Action == "Rejected")
        .subquery()
    )

    records = (
        db.session.query(
            Attendance.AttendanceID,
            Attendance.EmployeeID,
            Attendance.Date,
            Attendance.CheckInTime,
            Attendance.CheckOutTime,
            subquery.c.ApprovedBy,
            subquery.c.ApprovedAt,
            subquery.c.Note,
        )
        .join(AttendanceApprovalStatus, Attendance.AttendanceID == AttendanceApprovalStatus.AttendanceID)
        .join(subquery, Attendance.AttendanceID == subquery.c.AttendanceID)
        .filter(AttendanceApprovalStatus.Status == "Rejected")
        .order_by(Attendance.Date.desc(), Attendance.EmployeeID)
        .all()
    )

    return render_template("attendance/attendance_rejected_list.html", records=records)


@attendance_rejected_bp.route("/attendance/rejected/resubmit", methods=["POST"])
@login_required
@check_permission("attendance", "update")
def resubmit_rejected_attendance():
    ids = request.form.getlist("attendance_ids")
    if not ids:
        flash("⚠️ Bạn chưa chọn dòng nào để chấm lại!", "warning")
        return redirect(url_for("attendance_rejected.list_rejected_attendance"))

    updated = 0
    for aid in ids:
        status = AttendanceApprovalStatus.query.filter_by(AttendanceID=aid).first()
        if status and status.Status == "Rejected":
            status.Status = "Pending"
            status.LastLevel = None
            status.LastAction = None
            status.LastModifiedBy = session.get("username")
            status.LastModifiedAt = None
            updated += 1

    db.session.commit()
    flash(f"✅ Đã chấm lại {updated} dòng. Trạng thái đã trở lại Pending.", "success")
    return redirect(url_for("attendance_rejected.list_rejected_attendance"))


@attendance_rejected_bp.route("/attendance/rejected/edit/<int:attendance_id>", methods=["GET", "POST"])
@login_required
@check_permission("attendance", "update")
def edit_rejected_attendance(attendance_id):
    attendance = Attendance.query.filter_by(AttendanceID=attendance_id).first()
    status = AttendanceApprovalStatus.query.filter_by(AttendanceID=attendance_id).first()

    if not attendance or not status or status.Status != "Rejected":
        flash("⚠️ Không thể sửa bản ghi không tồn tại hoặc không bị từ chối.", "danger")
        return redirect(url_for("attendance_rejected.list_rejected_attendance"))

    if request.method == "POST":
        old_data = copy.deepcopy(attendance)

        attendance.Date = request.form["Date"]
        attendance.CheckInTime = request.form["CheckInTime"]
        attendance.CheckOutTime = request.form["CheckOutTime"]
        attendance.Note = request.form["Note"]
        from utils.attendance_utils import update_ot_and_working_hours

        update_ot_and_working_hours(attendance)

        status.Status = "Pending"
        status.LastLevel = None
        status.LastAction = None
        status.LastModifiedBy = session.get("username")
        status.LastModifiedAt = None

        log_attendance_change_from_objects(
            attendance_before=old_data,
            attendance_after=attendance,
            edited_by=session.get("full_name", session.get("user_id", "unknown")),
            editor_role=session.get("role", "unknown"),
            source="Web UI",
            change_type="Manual Edit",
        )

        db.session.commit()
        flash("✅ Đã cập nhật và gửi lại duyệt!", "success")
        return redirect(url_for("attendance_rejected.list_rejected_attendance"))

    return render_template("attendance/attendance_rejected_edit_form.html", record=attendance)
