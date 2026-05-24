from flask import Blueprint, render_template, request
from datetime import datetime
from models import db
from models.attendance.attendance_model import Attendance
from models.hr.hr_profiles import HRProfile

attendance_avg_shift_bp = Blueprint("attendance_avg_shift", __name__)


@attendance_avg_shift_bp.route("/attendance/stats/shift")
def attendance_avg_by_shift():
    month = int(request.args.get("month", datetime.today().month))
    year = int(request.args.get("year", datetime.today().year))

    shift_names = {1: "Ca sáng", 2: "Ca chiều", 3: "Ca đêm"}

    # Truy vấn dữ liệu theo ca
    records = Attendance.query.filter(
        db.extract("month", Attendance.Date) == month, db.extract("year", Attendance.Date) == year
    ).all()

    shift_stats = {}
    for r in records:
        name = shift_names.get(r.ShiftID, f"Ca {r.ShiftID}")
        if name not in shift_stats:
            shift_stats[name] = {"total": 0, "count": 0}
        shift_stats[name]["total"] += r.WorkingHours or 0
        shift_stats[name]["count"] += 1

    labels = list(shift_stats.keys())
    values = [
        round(shift_stats[k]["total"] / shift_stats[k]["count"], 2) if shift_stats[k]["count"] > 0 else 0
        for k in labels
    ]

    return render_template("attendance/attendance_avg_shift.html", labels=labels, values=values, month=month, year=year)


@attendance_avg_shift_bp.route("/attendance/stats/heatmap")
def attendance_heatmap():
    month = int(request.args.get("month", datetime.today().month))
    year = int(request.args.get("year", datetime.today().year))

    # Lấy tất cả nhân viên có dữ liệu trong tháng đó
    employees = (
        db.session.query(Attendance.EmployeeID, HRProfile.FullName, Attendance.Date, Attendance.WorkingHours)
        .join(HRProfile, HRProfile.EmployeeID == Attendance.EmployeeID)
        .filter(db.extract("month", Attendance.Date) == month, db.extract("year", Attendance.Date) == year)
        .all()
    )

    emp_map = {emp.EmployeeID: emp.FullName for emp in employees}
    days = list(range(1, 32))

    # Khởi tạo ma trận dữ liệu heatmap: emp_id -> [công theo từng ngày]
    heatmap = {emp_id: [0 for _ in days] for emp_id in emp_map.keys()}

    records = Attendance.query.filter(
        db.extract("month", Attendance.Date) == month, db.extract("year", Attendance.Date) == year
    ).all()

    for r in records:
        d = r.Date.day
        if r.EmployeeID in heatmap:
            heatmap[r.EmployeeID][d - 1] += r.WorkingHours or 0

    return render_template(
        "attendance/attendance_heatmap.html", employees=emp_map, days=days, heatmap=heatmap, month=month, year=year
    )


@attendance_avg_shift_bp.route("/attendance/stats/line")
def attendance_line_by_day():
    month = int(request.args.get("month", datetime.today().month))
    year = int(request.args.get("year", datetime.today().year))

    daily_stats = {d: 0 for d in range(1, 32)}
    counts = {d: 0 for d in range(1, 32)}

    records = Attendance.query.filter(
        db.extract("month", Attendance.Date) == month, db.extract("year", Attendance.Date) == year
    ).all()

    for r in records:
        day = r.Date.day
        daily_stats[day] += r.WorkingHours or 0
        counts[day] += 1

    labels = [str(d) for d in range(1, 32)]
    values = [round(daily_stats[d] / counts[d], 2) if counts[d] else 0 for d in range(1, 32)]

    return render_template(
        "attendance/attendance_line_chart.html", labels=labels, values=values, month=month, year=year
    )
