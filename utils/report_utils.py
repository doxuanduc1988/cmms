from flask import render_template, current_app
from weasyprint import HTML
from io import BytesIO
import os


def render_resume_pdf(profile, education_list, work_history_list, dependents, salary_history, sections):
    # Lấy đường dẫn tuyệt đối của ảnh nhân viên (nếu có)
    photo_url = None
    if profile.Photo:
        photo_path = os.path.join(current_app.static_folder, "uploads", "hr_pics", profile.Photo)
        if os.path.exists(photo_path):
            photo_url = photo_path

    html_out = render_template(
        "reports/hr/report_resume.html",
        profile=profile,
        education_list=education_list,
        work_history_list=work_history_list,
        dependents=dependents,
        salary_history=salary_history,
        selected_sections=sections,
        #        photo_path=photo_url  # ✅ truyền vào template
        photo_path=photo_path,
    )

    pdf_io = BytesIO()
    HTML(string=html_out, base_url=current_app.root_path).write_pdf(pdf_io)
    pdf_io.seek(0)
    return pdf_io
