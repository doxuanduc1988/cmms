from flask import Blueprint, render_template, request
from extensions import db
from models.attendance.attendance_model import Attendance
from models.attendance.approval_status import AttendanceApprovalStatus
from models.hr.department_model import Department
from datetime import datetime
from sqlalchemy import extract
from utils.permission_utils import check_permission
from flask_login import login_required


attendance_dashboard_bp = Blueprint("attendance_dashboard", __name__)


@attendance_dashboard_bp.route("/attendance/approval/dashboard")
@login_required
@check_permission("attendance", "read")
def approval_dashboard():
    selected_month = int(request.args.get("month", datetime.today().month))
    selected_year = int(request.args.get("year", datetime.today().year))
    selected_status = request.args.get("status", "")
    selected_dept = request.args.get("department", "")

    query = (
        db.session.query(
            Attendance.AttendanceID,
            Attendance.EmployeeID,
            Attendance.Date,
            Attendance.CheckInTime,
            Attendance.CheckOutTime,
            Attendance.DepartmentCode,
            AttendanceApprovalStatus.Status,
            AttendanceApprovalStatus.LastLevel,
            AttendanceApprovalStatus.LastModifiedBy,
            AttendanceApprovalStatus.LastModifiedAt,
        )
        .join(AttendanceApprovalStatus, Attendance.AttendanceID == AttendanceApprovalStatus.AttendanceID)
        .filter(extract("month", Attendance.Date) == selected_month, extract("year", Attendance.Date) == selected_year)
    )

    if selected_status:
        query = query.filter(AttendanceApprovalStatus.Status == selected_status)
    if selected_dept:
        query = query.filter(Attendance.DepartmentCode == selected_dept)

    records = query.order_by(Attendance.Date.desc(), Attendance.EmployeeID).all()
    departments = Department.query.order_by(Department.DepartmentName).all()
    current_year = datetime.today().year

    return render_template(
        "attendance/attendance_approval_dashboard.html",
        records=records,
        month=selected_month,
        year=selected_year,
        current_year=current_year,
        departments=departments,
        selected_dept=selected_dept,
        selected_status=selected_status,
    )
