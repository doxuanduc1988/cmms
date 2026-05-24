from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from utils.permission_utils import check_permission

from models.attendance.attendance_model import Attendance
from models.hr.hr_profiles import HRProfile
from models.hr.department_model import Department
from extensions import db
from sqlalchemy import func
from datetime import datetime

attendance_grid_bp = Blueprint("attendance_grid", __name__, url_prefix="/attendance/grid")


# Hiển thị bảng công dạng Grid
@attendance_grid_bp.route("/", methods=["GET", "POST"])
@login_required
@check_permission("attendance", "read")
def bulk_grid_attendance():
    departments = Department.query.all()
    selected_month = None
    selected_department = None
    report = []

    if request.method == "POST":
        selected_month = request.form.get("month")  # yyyy-mm
        selected_department = request.form.get("department_code")

        if selected_month:
            year, month = map(int, selected_month.split("-"))

            query = (
                db.session.query(
                    Attendance.EmployeeID,
                    HRProfile.FullName,
                    HRProfile.DepartmentCode,
                    Attendance.Date,
                    Attendance.Status,
                    Attendance.WorkingHours,
                )
                .join(HRProfile, HRProfile.EmployeeID == Attendance.EmployeeID)
                .filter(func.year(Attendance.Date) == year, func.month(Attendance.Date) == month)
            )

            if selected_department:
                query = query.filter(Attendance.DepartmentCode == selected_department)

            report = query.all()

    return render_template(
        "attendance/bulk_grid_attendance.html",
        departments=departments,
        report=report,
        selected_month=selected_month,
        selected_department=selected_department,
    )


# Route để update trực tiếp ô chấm công
@attendance_grid_bp.route("/update", methods=["POST"])
@login_required
@check_permission("attendance", "update")
def update_cell():
    data = request.get_json()
    employee_id = data.get("employee_id")
    date_str = data.get("date")
    value = data.get("value")

    if not employee_id or not date_str:
        return jsonify({"success": False, "message": "Thiếu dữ liệu"}), 400

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"success": False, "message": "Ngày không hợp lệ"}), 400

    attendance = Attendance.query.filter_by(EmployeeID=employee_id, Date=date).first()
    if not attendance:
        # Truy vấn lấy DepartmentCode từ HRProfile
        hr_profile = HRProfile.query.filter_by(EmployeeID=employee_id).first()
        department_code = hr_profile.DepartmentCode if hr_profile else None

        attendance = Attendance(EmployeeID=employee_id, Date=date, DepartmentCode=department_code, Status="Working")
        db.session.add(attendance)

    try:
        if value is None or value.strip() == "":
            attendance.WorkingHours = None
            attendance.Status = "Absent"
        else:
            try:
                attendance.WorkingHours = float(value)
                if attendance.WorkingHours > 0:
                    attendance.Status = "Working"
                else:
                    attendance.Status = "Absent"
            except ValueError:
                return jsonify({"success": False, "message": "Dữ liệu không hợp lệ!"}), 400
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
