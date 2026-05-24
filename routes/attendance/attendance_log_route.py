from flask import Blueprint, render_template, request
from models.attendance.attendance_edit_log import AttendanceEditLog
from models.hr.hr_profiles import HRProfile
from models.hr.department_model import Department
from models.attendance.attendance_model import Attendance
from extensions import db
from datetime import datetime

attendance_log_bp = Blueprint("attendance_log", __name__, url_prefix="/attendance/log")


@attendance_log_bp.route("/", methods=["GET", "POST"])
def view_logs():
    logs = []
    employee_id = None
    start_date = None
    end_date = None
    change_type = None
    department_code = None

    departments = Department.query.all()

    if request.method == "POST":
        employee_id = request.form.get("employee_id")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        change_type = request.form.get("change_type")

        query = db.session.query(AttendanceEditLog)

        if employee_id:
            query = query.filter(AttendanceEditLog.EmployeeID == employee_id)

        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(AttendanceEditLog.EditedAt >= start)
            except:
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d")
                query = query.filter(AttendanceEditLog.EditedAt <= end)
            except:
                pass

        if change_type:
            query = query.filter(AttendanceEditLog.ChangeType == change_type)

        logs = query.order_by(AttendanceEditLog.EditedAt.desc()).all()
    else:
        logs = db.session.query(AttendanceEditLog).order_by(AttendanceEditLog.EditedAt.desc()).all()

    return render_template(
        "attendance/attendance_log_form.html",
        logs=logs,
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        department_code=department_code,
        change_type=change_type,
        departments=departments,
    )
