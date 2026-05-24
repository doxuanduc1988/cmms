from datetime import datetime

from flask import Blueprint, render_template, request
from flask_login import login_required

from models import db
from models.attendance.attendance_model import Attendance
from models.hr.hr_profiles import HRProfile
from utils.permission_utils import check_permission

attendance_stats_bp = Blueprint("attendance_stats", __name__)


@attendance_stats_bp.route("/attendance/stats/department", methods=["GET"])
@login_required
@check_permission("attendance", "read")
def attendance_stats():
    month = int(request.args.get("month", datetime.today().month))
    year = int(request.args.get("year", datetime.today().year))

    # Lấy danh sách phòng ban
    departments = db.session.query(HRProfile.DepartmentCode).distinct().all()
    departments = sorted([d[0] for d in departments if d[0]])

    # Tạo dict lưu tổng công và OT theo phòng ban
    stats = {dept: {"working": 0, "ot": 0} for dept in departments}

    # Truy vấn Attendance có join với HRProfiles để lấy Department
    records = (
        db.session.query(Attendance, HRProfile)
        .join(HRProfile, Attendance.EmployeeID == HRProfile.EmployeeID)
        .filter(db.extract("month", Attendance.Date) == month, db.extract("year", Attendance.Date) == year)
        .all()
    )

    for att, hr in records:
        dept = hr.DepartmentCode or "Khác"
        if dept not in stats:
            stats[dept] = {"working": 0, "ot": 0}
        stats[dept]["working"] += att.WorkingHours or 0
        stats[dept]["ot"] += att.OvertimeHours or 0

    labels = list(stats.keys())
    working_data = [round(stats[d]["working"], 1) for d in labels]
    ot_data = [round(stats[d]["ot"], 1) for d in labels]

    return render_template(
        "attendance/attendance_stats.html",
        labels=labels,
        working_data=working_data,
        ot_data=ot_data,
        month=month,
        year=year,
    )
