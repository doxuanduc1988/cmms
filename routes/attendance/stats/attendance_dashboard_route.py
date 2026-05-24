from flask import Blueprint, render_template, request
from models import db
from models.attendance.attendance_model import Attendance
from models.hr.hr_profiles import HRProfile
from sqlalchemy import extract, func
from collections import defaultdict

stats_dashboard_bp = Blueprint("stats_dashboard", __name__, url_prefix="/attendance/stats")


@stats_dashboard_bp.route("/dashboard")
def attendance_dashboard():
    month = int(request.args.get("month", 5))
    year = int(request.args.get("year", 2025))

    # Biểu đồ theo ca
    shift_data = (
        db.session.query(Attendance.ShiftID, func.avg(Attendance.WorkingHours))
        .filter(extract("month", Attendance.Date) == month, extract("year", Attendance.Date) == year)
        .group_by(Attendance.ShiftID)
        .order_by(Attendance.ShiftID)
        .all()
    )
    shift_labels = [f"Ca {s[0]}" for s in shift_data]
    shift_values = [round(s[1], 2) for s in shift_data]

    # Biểu đồ theo ngày
    line_data = (
        db.session.query(extract("day", Attendance.Date), func.avg(Attendance.WorkingHours))
        .filter(extract("month", Attendance.Date) == month, extract("year", Attendance.Date) == year)
        .group_by(extract("day", Attendance.Date))
        .order_by(extract("day", Attendance.Date))
        .all()
    )
    line_labels = [int(d[0]) for d in line_data]
    line_values = [round(d[1], 2) for d in line_data]

    # Heatmap
    days = list(range(1, 32))
    raw = (
        db.session.query(
            Attendance.EmployeeID,
            HRProfile.FullName,
            extract("day", Attendance.Date),
            func.sum(Attendance.WorkingHours),
        )
        .join(HRProfile, HRProfile.EmployeeID == Attendance.EmployeeID)
        .filter(extract("month", Attendance.Date) == month, extract("year", Attendance.Date) == year)
        .group_by(Attendance.EmployeeID, HRProfile.FullName, extract("day", Attendance.Date))
        .all()
    )

    employees = {}
    heatmap = defaultdict(lambda: [0] * 31)
    for emp_id, full_name, day, hours in raw:
        employees[emp_id] = full_name
        heatmap[emp_id][int(day) - 1] = round(hours, 1)

    return render_template(
        "attendance/attendance_dashboard.html",
        month=month,
        year=year,
        shift_labels=shift_labels,
        shift_values=shift_values,
        line_labels=line_labels,
        line_values=line_values,
        employees=employees,
        heatmap=heatmap,
        days=days,
    )
