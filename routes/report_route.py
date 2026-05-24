# routes/report_route.py
from flask import Blueprint, render_template, send_file, abort, current_app
from datetime import datetime
from io import BytesIO
from sqlalchemy import func
import os, shutil

from extensions import db
from models.hr.department_model import Department
from models.hr.hr_profiles import HRProfile
from flask_login import login_required
from utils.permission_utils import check_permission

# 1) CHỈ MỘT blueprint với tên "hr_report"
hr_report_bp = Blueprint("hr_report", __name__, url_prefix="/reports")


# 2) Truy vấn chung
def _query_employees_by_department():
    return (
        db.session.query(
            Department.DepartmentCode.label("DeptCode"),
            Department.DepartmentName.label("DeptName"),
            func.count(HRProfile.EmployeeID).label("Total"),
        )
        .select_from(HRProfile)
        .outerjoin(Department, Department.DepartmentCode == HRProfile.DepartmentCode)
        .group_by(Department.DepartmentCode, Department.DepartmentName)
        .order_by(Department.DepartmentName.asc())
        .all()
    )


# 3) Các route, mỗi endpoint CHỈ ĐỊNH danh tính rõ ràng
@hr_report_bp.route("/employees_by_department", endpoint="employees_by_department")
@login_required
@check_permission("hr", "read")
def employees_by_department():
    stats = _query_employees_by_department()
    total_all = sum(int(r.Total or 0) for r in stats)
    return render_template("reports/employees_by_department.html", stats=stats, total_all=total_all)


@hr_report_bp.route("/employees_by_department/print", endpoint="employees_by_department_print")
@login_required
@check_permission("hr", "read")
def employees_by_department_print():
    stats = _query_employees_by_department()
    total_all = sum(int(r.Total or 0) for r in stats)
    return render_template(
        "reports/employees_by_department_print.html", stats=stats, total_all=total_all, printed_at=datetime.now()
    )


def _find_wkhtmltopdf():
    # Ưu tiên config app → ENV → PATH → vị trí phổ biến
    p = current_app.config.get("WKHTMLTOPDF_PATH")
    if p and os.path.exists(p):
        return p
    p = os.environ.get("WKHTMLTOPDF_PATH")
    if p and os.path.exists(p):
        return p
    p = shutil.which("wkhtmltopdf")
    if p:
        return p
    for c in (
        r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
        r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
    ):
        if os.path.exists(c):
            return c
    return None


@hr_report_bp.route("/employees_by_department/pdf", endpoint="employees_by_department_pdf")
@login_required
@check_permission("hr", "read")
def employees_by_department_pdf():
    try:
        import pdfkit
    except Exception:
        abort(500, "Thiếu thư viện pdfkit. Chạy: pip install pdfkit")

    wkhtml_path = _find_wkhtmltopdf()
    if not wkhtml_path:
        abort(500, "Không tìm thấy wkhtmltopdf.exe. Cài wkhtmltopdf và/hoặc đặt WKHTMLTOPDF_PATH.")

    config = pdfkit.configuration(wkhtmltopdf=wkhtml_path)

    html = render_template(
        "reports/employees_by_department_print.html",
        stats=_query_employees_by_department(),
        total_all=None,
        printed_at=datetime.now(),
    )

    pdf_bytes = pdfkit.from_string(
        html,
        False,
        configuration=config,
        options={
            "encoding": "utf-8",
            "page-size": "A4",
            "margin-top": "10mm",
            "margin-right": "10mm",
            "margin-bottom": "10mm",
            "margin-left": "10mm",
        },
    )
    return send_file(
        BytesIO(pdf_bytes),
        download_name=f"NhanSuTheoPhong_{datetime.now():%Y%m%d}.pdf",
        as_attachment=True,
        mimetype="application/pdf",
    )
