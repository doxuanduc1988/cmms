from flask import Blueprint, render_template, request
from models.hr.hr_profiles import HRProfile
from models.attendance.attendance_model import Attendance
from models.hr.department_model import Department
from extensions import db
from datetime import datetime

attendance_unmarked_bp = Blueprint("attendance_unmarked", __name__, url_prefix="/attendance/unmarked")


@attendance_unmarked_bp.route("/", methods=["GET", "POST"])
def view_unmarked_attendance():
    employees = []
    selected_date = None
    selected_dept = None

    departments = Department.query.all()

    if request.method == "POST":
        selected_date = request.form.get("date")
        selected_dept = request.form.get("department_code")

        if selected_date and selected_dept:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()

            # Tìm tất cả nhân viên thuộc phòng được chọn
            query = HRProfile.query.filter(HRProfile.DepartmentCode == selected_dept)

            all_employees = query.all()
            marked_ids = db.session.query(Attendance.EmployeeID).filter(Attendance.Date == date_obj).all()
            marked_ids = {e[0] for e in marked_ids}

            # Lọc ra nhân viên chưa có công trong ngày
            employees = [e for e in all_employees if e.EmployeeID not in marked_ids]

    return render_template(
        "attendance/attendance_unmarked_list.html",
        employees=employees,
        selected_date=selected_date,
        selected_dept=selected_dept,
        departments=departments,
    )
