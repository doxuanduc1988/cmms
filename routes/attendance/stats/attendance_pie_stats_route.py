from datetime import datetime

from flask import Blueprint, render_template, request
from flask_login import login_required

from models import db
from models.attendance.attendance_model import Attendance
from utils.permission_utils import check_permission

attendance_pie_bp = Blueprint("attendance_pie", __name__)


@attendance_pie_bp.route("/attendance/stats/pie")
@login_required
@check_permission("attendance", "read")
def attendance_pie():
    month = int(request.args.get("month", datetime.today().month))
    year = int(request.args.get("year", datetime.today().year))

    stats = {"Working": 0, "OT": 0, "Leave": 0, "Absent": 0}

    records = Attendance.query.filter(
        db.extract("month", Attendance.Date) == month, db.extract("year", Attendance.Date) == year
    ).all()

    for r in records:
        status = (r.Status or "").lower()
        if "ot" in status:
            stats["OT"] += r.OvertimeHours or 0
        elif "leave" in status or "phép" in status:
            stats["Leave"] += r.WorkingHours or 0
        elif "off" in status or "nghỉ" in status:
            stats["Absent"] += r.WorkingHours or 0
        else:
            stats["Working"] += r.WorkingHours or 0

    labels = list(stats.keys())
    values = list(stats.values())

    return render_template("attendance/attendance_pie_stats.html", labels=labels, values=values, month=month, year=year)
