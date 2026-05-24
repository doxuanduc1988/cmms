from flask import Blueprint, send_file, request

# from weasyprint import HTML
from io import BytesIO
import pandas as pd
from datetime import datetime
from models import db
from models.attendance.attendance_model import Attendance
from models.hr.hr_profiles import HRProfile

attendance_export_bp = Blueprint("attendance_export", __name__)
attendance_pdf_bp = Blueprint("attendance_pdf", __name__)


@attendance_export_bp.route("/export_monthly_excel", methods=["GET"])
def export_excel():
    try:
        month = int(request.args.get("month", "").strip())
    except (ValueError, TypeError):
        month = datetime.today().month

    try:
        year = int(request.args.get("year", "").strip())
    except (ValueError, TypeError):
        year = datetime.today().year

    employees = HRProfile.query.order_by(HRProfile.DepartmentCode, HRProfile.EmployeeID).all()

    attendance_records = Attendance.query.filter(
        db.extract("month", Attendance.Date) == month, db.extract("year", Attendance.Date) == year
    ).all()

    data = {}
    for emp in employees:
        row = {
            "Họ tên": emp.FullName,
            "Phòng ban": emp.DepartmentCode,
        }
        for day in range(1, 32):
            row[f"{day:02d}"] = ""
        data[emp.EmployeeID] = row

    for record in attendance_records:
        emp_id = record.EmployeeID
        day = record.Date.day
        if emp_id in data:
            val = ""
            if record.Status == "OT":
                val = f"OT: {record.OvertimeHours:.1f}"
            elif record.OvertimeHours:
                val = f"{record.WorkingHours:.1f}\nOT:{record.OvertimeHours:.1f}"
            else:
                val = f"{record.WorkingHours:.1f}"
            data[emp_id][f"{day:02d}"] = val

    df = pd.DataFrame.from_dict(data, orient="index")
    df.index.name = "Mã NV"

    output = BytesIO()
    df.to_excel(output, index=True)
    output.seek(0)

    filename = f"ChamCong_{month:02d}_{year}.xlsx"
    return send_file(output, download_name=filename, as_attachment=True)
