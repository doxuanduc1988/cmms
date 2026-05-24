from flask import Blueprint, render_template, request
from models.hr.hr_profiles import HRProfile
from models.attendance.attendance_model import Attendance
from models.attendance.crew_model import CrewDefinition
from models.attendance.shift_model import ShiftDefinition
from sqlalchemy import extract
from extensions import db
from datetime import datetime

attendance_summary_bp = Blueprint("attendance_summary", __name__, url_prefix="/attendance")


@attendance_summary_bp.route("/monthly_summary", methods=["GET"])
def monthly_summary():
    selected_month = int(request.args.get("month", datetime.today().month))
    selected_year = int(request.args.get("year", datetime.today().year))
    department = request.args.get("department")
    crew = request.args.get("crew")
    shift = request.args.get("shift")

    query = HRProfile.query
    if department:
        query = query.filter(HRProfile.DepartmentCode == department)
    if crew:
        query = query.filter(HRProfile.CrewID == crew)

    employees = query.all()
    emp_map = {e.EmployeeID: e.FullName for e in employees}
    emp_list = list(emp_map.keys())

    data = {
        emp_id: {
            "name": emp_map[emp_id],
            "days": {d: {"work": 0, "ot": 0} for d in range(1, 32)},
            "total_work": 0,
            "total_ot": 0,
        }
        for emp_id in emp_list
    }

    from models.attendance.approval_status import AttendanceApprovalStatus

    records = (
        db.session.query(Attendance)
        .join(AttendanceApprovalStatus, Attendance.AttendanceID == AttendanceApprovalStatus.AttendanceID)
        .filter(
            AttendanceApprovalStatus.Status == "Approved",
            extract("month", Attendance.Date) == selected_month,
            extract("year", Attendance.Date) == selected_year,
            Attendance.EmployeeID.in_(emp_list),
        )
    )
    if department:
        records = records.filter(Attendance.DepartmentCode == department)
    if crew:
        records = records.filter(Attendance.CrewID == crew)
    if shift != "" and shift is not None:
        records = records.filter(Attendance.ShiftID == int(shift))

    for r in records:
        emp_id = r.EmployeeID
        if emp_id not in data:
            continue
        day = r.Date.day
        if data[emp_id]["days"][day]["work"] == 0:
            data[emp_id]["days"][day]["work"] = 1
            data[emp_id]["total_work"] += 1
        ot = r.OvertimeHours or 0
        data[emp_id]["days"][day]["ot"] += ot
        data[emp_id]["total_ot"] += ot

    department_list = (
        db.session.query(HRProfile.DepartmentCode).distinct().filter(HRProfile.DepartmentCode != None).all()
    )
    department_list = [(code, f"Phòng {code}") for (code,) in department_list]

    crew_raw = db.session.query(CrewDefinition.CrewID, CrewDefinition.CrewName).all()
    crew_list = [(str(cid), cname) for cid, cname in crew_raw]

    shift_raw = db.session.query(ShiftDefinition.ShiftID, ShiftDefinition.ShiftName).all()
    shift_list = [(str(sid), sname) for sid, sname in shift_raw]

    # Gắn DepartmentCode cho từng nhân viên
    emp_profiles = {e.EmployeeID: e for e in employees}
    for emp_id in data:
        profile = emp_profiles.get(emp_id)
        data[emp_id]["department"] = profile.DepartmentCode if profile else ""

    # Sắp xếp theo phòng ban ưu tiên
    priority_order = ["TCHC", "PKTAT", "KHTC", "PTM", "PXVN", "PXSC", "PXNL"]

    def department_priority(code):
        try:
            return priority_order.index(code)
        except ValueError:
            return len(priority_order)

    data = dict(sorted(data.items(), key=lambda x: (department_priority(x[1].get("department", "")), x[0])))

    return render_template(
        "attendance/attendance_monthly_summary.html",
        data=data,
        selected_month=selected_month,
        selected_year=selected_year,
        department_list=department_list,
        crew_list=crew_list,
        shift_list=shift_list,
    )
