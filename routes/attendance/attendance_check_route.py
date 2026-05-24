from flask import Blueprint, render_template, request, session, abort
from models.attendance.attendance_model import Attendance
from models.hr.hr_profiles import HRProfile
from models.hr.department_model import Department
from models.attendance.shift_model import ShiftDefinition
from models.attendance.crew_model import CrewDefinition
from extensions import db
from datetime import datetime

from utils.attendance_utils import update_ot_and_working_hours

attendance_check_bp = Blueprint("attendance_check", __name__, url_prefix="/attendance/check")


@attendance_check_bp.route("/", methods=["GET", "POST"])
def check_attendance():
    role = session.get("role", "").lower()
    if role not in ("admin", "nhansu", "hanhchinh"):
        abort(403)
    departments = Department.query.all()
    shifts = ShiftDefinition.query.all()
    crews = CrewDefinition.query.all()
    results = []

    if request.method == "POST":
        selected_date = request.form.get("selected_date")
        department_code = request.form.get("department_code")
        shift_id = request.form.get("shift_id")
        crew_id = request.form.get("crew_id")

        query = (
            db.session.query(
                Attendance.AttendanceID,
                Attendance.EmployeeID,
                HRProfile.FullName,
                Attendance.DepartmentCode,
                Attendance.CrewID,
                ShiftDefinition.ShiftName,
                Attendance.CheckInTime,
                Attendance.CheckOutTime,
                Attendance.Status,
                Attendance.Note,
            )
            .join(HRProfile, Attendance.EmployeeID == HRProfile.EmployeeID)
            .outerjoin(ShiftDefinition, Attendance.ShiftID == ShiftDefinition.ShiftID)
            .filter(Attendance.Date == selected_date)
        )

        if department_code:
            query = query.filter(Attendance.DepartmentCode == department_code)
        if shift_id:
            query = query.filter(Attendance.ShiftID == shift_id)
        if crew_id:
            query = query.filter(Attendance.CrewID == crew_id)

        results = query.all()

        # Cập nhật WorkingHours và Overtime nếu thiếu
        for row in results:
            att = Attendance.query.get(row.AttendanceID)
            if att and att.CheckInTime and att.CheckOutTime:
                if att.WorkingHours is None or att.OvertimeHours is None:
                    update_ot_and_working_hours(att)
        db.session.commit()

        return render_template(
            "attendance/attendance_check_result.html",
            results=results,
            selected_date=selected_date,
            department_code=department_code,
            shift_id=shift_id,
            crew_id=crew_id,
        )

    return render_template("attendance/attendance_check_form.html", departments=departments, shifts=shifts, crews=crews)
