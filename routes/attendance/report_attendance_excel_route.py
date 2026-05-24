from flask import Blueprint, request, send_file
from models.attendance.attendance_model import Attendance
from models.hr.hr_profiles import HRProfile
from models.attendance.crew_model import CrewDefinition
from models.attendance.shift_model import ShiftDefinition
from models.hr.department_model import Department
from extensions import db
from datetime import datetime
import pandas as pd
from io import BytesIO

report_bp = Blueprint("report", __name__, url_prefix="/attendance/report")


@report_bp.route("/export_excel")
def export_attendance_excel():
    selected_date = request.args.get("selected_date")
    department_code = request.args.get("department_code")
    shift_id = request.args.get("shift_id")
    crew_id = request.args.get("crew_id")

    if not selected_date:
        return "Thiếu ngày cần xuất báo cáo", 400

    date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()

    query = (
        db.session.query(
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
        .outerjoin(ShiftDefinition, ShiftDefinition.ShiftID == Attendance.ShiftID)
    )

    query = query.filter(Attendance.Date == date_obj)

    if department_code:
        query = query.filter(Attendance.DepartmentCode == department_code)
    if shift_id:
        query = query.filter(Attendance.ShiftID == shift_id)
    if crew_id:
        query = query.filter(Attendance.CrewID == crew_id)

    results = query.all()

    if not results:
        return "Không có dữ liệu để xuất", 404

    # Đưa dữ liệu vào DataFrame
    df = pd.DataFrame(
        results, columns=["Mã NV", "Họ tên", "Phòng", "Kíp", "Ca", "Giờ vào", "Giờ ra", "Trạng thái", "Ghi chú"]
    )

    # Tính tổng số nhân viên và số theo từng trạng thái
    total_count = len(df)
    status_summary = df["Trạng thái"].value_counts().to_dict()

    # Tạo dòng tổng cộng đầu tiên
    summary_lines = [f"Tổng số nhân viên: {total_count}"]
    for status, count in status_summary.items():
        summary_lines.append(f"{status}: {count}")

    # Tạo file Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Báo cáo")
        writer.sheets["Báo cáo"] = worksheet

        # Ghi dòng tổng cộng trên cùng
        for row_num, line in enumerate(summary_lines):
            worksheet.write(row_num, 0, line)

        # Ghi DataFrame vào sau dòng tổng cộng
        df.to_excel(writer, index=False, startrow=len(summary_lines) + 1, sheet_name="Báo cáo")

    output.seek(0)
    filename = f"baocao_chamcong_{selected_date}.xlsx"
    return send_file(
        output,
        download_name=filename,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
