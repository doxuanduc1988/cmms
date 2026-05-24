# routes/report_resume.py
# -*- coding: utf-8 -*-
"""
In hồ sơ (resume/CV) nhân sự dưới dạng PDF.
Blueprint này phải có tên DUY NHẤT để không va chạm với blueprint 'hr_report' ở routes/report_route.py.
"""

from flask import Blueprint, request, send_file, abort
from models import (
    HRProfile,
    HREducationHistory,
    HRWorkHistory,
    HRDependent,
    HRSalaryHistory,
)
from utils.report_utils import render_resume_pdf
from flask_login import login_required
from utils.permission_utils import check_permission

# ✅ Đặt tên blueprint DUY NHẤT, KHÔNG trùng với 'hr_report'
#    Thêm url_prefix để gom các route báo cáo HR vào chung một prefix.
hr_report_resume_bp = Blueprint(
    "hr_report_resume", __name__, url_prefix="/hr-report"  # <-- tên endpoint prefix: hr_report_resume.*
)


@hr_report_resume_bp.route("/resume/<string:employee_id>", methods=["GET", "POST"])
@login_required
@check_permission("hr", "read")
def print_resume(employee_id: str):
    """
    Tạo và trả về file PDF hồ sơ nhân sự.
    - GET: dùng danh sách sections mặc định (profile, education, work, salary, family)
            hoặc lấy từ query string (?sections=profile&sections=work...)
    - POST: lấy sections từ form (request.form.getlist("sections"))
    """

    # 1) Lấy hồ sơ chính
    profile = HRProfile.query.filter_by(EmployeeID=employee_id).first()
    if not profile:
        # Nếu không có nhân sự -> trả về 404
        abort(404)

    # 2) Xác định danh sách sections
    if request.method == "POST":
        sections = request.form.getlist("sections")
    else:
        # GET: lấy từ query string nếu có, nếu không dùng mặc định
        sections = request.args.getlist("sections")
        if not sections:
            # Mặc định: in đầy đủ hồ sơ
            sections = ["profile", "education", "work", "salary", "family"]

    # 3) Lấy dữ liệu phụ theo sections
    education_list = HREducationHistory.query.filter_by(EmployeeID=employee_id).all() if "education" in sections else []
    work_history_list = HRWorkHistory.query.filter_by(EmployeeID=employee_id).all() if "work" in sections else []
    dependents = HRDependent.query.filter_by(EmployeeID=employee_id).all() if "family" in sections else []
    salary_history = HRSalaryHistory.query.filter_by(EmployeeID=employee_id).all() if "salary" in sections else []

    # 4) Gọi hàm render PDF (hàm này trả về đường dẫn/tệp BytesIO sẵn sàng gửi về)
    pdf_file = render_resume_pdf(
        profile=profile,
        education_list=education_list,
        work_history_list=work_history_list,
        dependents=dependents,
        salary_history=salary_history,
        sections=sections,
    )

    # 5) Trả về PDF
    return send_file(
        pdf_file,
        as_attachment=True,
        download_name=f"resume_{employee_id}.pdf",
        mimetype="application/pdf",
    )
