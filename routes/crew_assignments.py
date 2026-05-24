# routes/crew_assignments.py
# Viết lại file crew_assignments.py hoàn chỉnh:
# - Giữ Dual Listbox nhân sự trái/phải
# - Thêm dropdown lọc theo Phòng/Đơn vị
# - Vẫn có ô tìm kiếm Available Employees
# - Sử dụng 1 file crew_assignments.py duy nhất
# - DepartmentCode nếu thiếu -> 'WAITCODE'
# - JobPositionID nếu thiếu -> 66
# - StartDate -> ngày hôm nay
# - EndDate -> ngày hôm nay + 1 năm
# Sửa route /crew_assignments/manage:
# - So sánh danh sách nhân viên cũ/mới
# - Chỉ xóa nhân viên bị gỡ bỏ
# - Chỉ thêm nhân viên mới

from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models.hr.hr_profiles import HRProfile
from models.hr.department_model import Department
from models.attendance.crew_model import CrewDefinition
from models.crew_assignment import CrewAssignment
from models.hr.job_position_model import JobPosition
from datetime import datetime, timedelta
from utils.auth_utils import login_required
from utils.permission_utils import check_permission

crew_assignment_bp = Blueprint("crew_assignments", __name__, url_prefix="/crew_assignments")


# Danh sách CrewAssignments
@crew_assignment_bp.route("/", methods=["GET"])
@login_required
@check_permission("crew", "read")
def list_crew_assignments():
    department_code = request.args.get("department_code")
    crew_id = request.args.get("crew_id")

    query = (
        db.session.query(
            CrewAssignment,
            HRProfile.FullName,
            Department.DepartmentName,
            CrewDefinition.CrewName,
            JobPosition.JobPositionName,
        )
        .join(HRProfile, CrewAssignment.EmployeeID == HRProfile.EmployeeID)
        .join(Department, CrewAssignment.DepartmentCode == Department.DepartmentCode)
        .join(CrewDefinition, CrewAssignment.CrewID == CrewDefinition.CrewID)
        .outerjoin(JobPosition, CrewAssignment.JobPositionID == JobPosition.JobPositionID)
    )

    # Lọc theo DepartmentCode nếu có
    if department_code:
        query = query.filter(CrewAssignment.DepartmentCode == department_code)

    # Lọc theo CrewID nếu có
    if crew_id:
        query = query.filter(CrewAssignment.CrewID == crew_id)

    assignments = query.all()
    departments = Department.query.all()
    crews = CrewDefinition.query.all()

    return render_template("crew_assignments/list.html", assignments=assignments, departments=departments, crews=crews)


# Tạo mới CrewAssignment
@crew_assignment_bp.route("/create", methods=["GET", "POST"])
@login_required
@check_permission("crew", "create")
def create_crew_assignment():
    departments = Department.query.all()
    crews = CrewDefinition.query.all()
    employees = HRProfile.query.all()
    positions = JobPosition.query.all()
    from datetime import date

    today = date.today().strftime("%Y-%m-%d")

    if request.method == "POST":
        employee_id = request.form.get("employee_id")
        department_code = request.form.get("department_code") or 'WAITCODE'
        crew_id = request.form.get("crew_id")
        job_position_id = request.form.get("job_position_id") or 66
        start_date = request.form.get("start_date") or today
        end_date = request.form.get("end_date") or (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")

        assignment = CrewAssignment(
            EmployeeID=employee_id,
            DepartmentCode=department_code,
            CrewID=crew_id,
            JobPositionID=job_position_id,
            StartDate=start_date,
            EndDate=end_date,
        )

        db.session.add(assignment)
        db.session.commit()

        # 🔄 Đồng bộ CrewID vào HRProfiles
        profile = HRProfile.query.filter_by(EmployeeID=employee_id).first()
        if profile:
            profile.CrewID = crew_id
        db.session.commit()

        flash("Thêm mới phân công nhân sự thành công!", "success")
        return redirect(url_for("crew_assignments.list_crew_assignments"))

    return render_template(
        "crew_assignments/create.html",
        departments=departments,
        crews=crews,
        employees=employees,
        positions=positions,
        today=today,
    )


# Sửa CrewAssignment
@crew_assignment_bp.route("/edit/<int:assignment_id>", methods=["GET", "POST"])
@login_required
@check_permission("crew", "update")
def edit_crew_assignment(assignment_id):
    assignment = CrewAssignment.query.get_or_404(assignment_id)
    departments = Department.query.all()
    crews = CrewDefinition.query.all()
    employees = HRProfile.query.all()
    positions = JobPosition.query.all()

    if request.method == "POST":
        assignment.EmployeeID = request.form.get("employee_id")
        assignment.DepartmentCode = request.form.get("department_code") or 'WAITCODE'
        assignment.CrewID = request.form.get("crew_id")
        assignment.JobPositionID = request.form.get("job_position_id") or 66
        assignment.StartDate = request.form.get("start_date")
        assignment.EndDate = request.form.get("end_date")

        db.session.commit()

        # 🔄 Đồng bộ CrewID vào HRProfiles
        profile = HRProfile.query.filter_by(EmployeeID=assignment.EmployeeID).first()
        if profile:
            profile.CrewID = assignment.CrewID
        db.session.commit()

        flash("Cập nhật phân công nhân sự thành công!", "success")
        return redirect(url_for("crew_assignments.list_crew_assignments"))

    return render_template(
        "crew_assignments/edit.html",
        assignment=assignment,
        departments=departments,
        crews=crews,
        employees=employees,
        positions=positions,
    )


# Xóa CrewAssignment
@crew_assignment_bp.route("/delete/<int:assignment_id>", methods=["POST"])
@login_required
@check_permission("crew", "delete")
def delete_crew_assignment(assignment_id):
    assignment = CrewAssignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    flash("Xóa phân công nhân sự thành công!", "success")
    return redirect(url_for("crew_assignments.list_crew_assignments"))


@crew_assignment_bp.route("/manage", methods=["GET", "POST"])
@check_permission("crew", "update")
def manage_crew_assignments():
    crews = CrewDefinition.query.order_by(CrewDefinition.CrewName).all()
    departments = Department.query.order_by(Department.DepartmentName).all()
    job_positions = JobPosition.query.order_by(JobPosition.JobPositionName).all()

    selected_crew_id = request.args.get("crew_id") or request.form.get("crew_id")
    selected_department_code = request.args.get("department_code") or request.form.get("department_code")

    if request.method == "POST":
        employee_ids = request.form.getlist("employee_ids")
        for emp_id in employee_ids:
            assignment = CrewAssignment.query.filter_by(CrewID=selected_crew_id, EmployeeID=emp_id).first()
            if assignment:
                start_date = request.form.get(f"start_dates[{emp_id}]")
                end_date = request.form.get(f"end_dates[{emp_id}]")
                job_position_id = request.form.get(f"job_positions[{emp_id}]")

                if start_date:
                    assignment.StartDate = datetime.strptime(start_date, "%Y-%m-%d").date()
                if end_date:
                    assignment.EndDate = datetime.strptime(end_date, "%Y-%m-%d").date()
                if job_position_id:
                    assignment.JobPositionID = int(job_position_id)

        db.session.commit()
        flash("✅ Đã cập nhật thông tin Assigned thành công!", "success")
        return redirect(
            url_for(
                "crew_assignments.manage_crew_assignments",
                crew_id=selected_crew_id,
                department_code=selected_department_code,
            )
        )

    employees = []
    assigned_employee_ids = []
    assigned_data = {}

    if selected_crew_id:
        assignments = CrewAssignment.query.filter_by(CrewID=selected_crew_id).all()
        assigned_employee_ids = [a.EmployeeID for a in assignments]
        for a in assignments:
            assigned_data[a.EmployeeID] = {
                "StartDate": a.StartDate.strftime("%Y-%m-%d") if a.StartDate else "",
                "EndDate": a.EndDate.strftime("%Y-%m-%d") if a.EndDate else "",
                "JobPositionID": a.JobPositionID,
            }

        query = HRProfile.query
        if selected_department_code:
            query = query.filter(HRProfile.DepartmentCode == selected_department_code)
        employees = query.order_by(HRProfile.FullName).all()

    return render_template(
        "crew_assignments/crew_assignment_manage.html",
        crews=crews,
        departments=departments,
        job_positions=job_positions,
        selected_crew_id=selected_crew_id,
        selected_department_code=selected_department_code,
        employees=employees,
        assigned_employee_ids=assigned_employee_ids,
        assigned_data=assigned_data,
    )


from flask import send_file
import pandas as pd
from fpdf import FPDF
from io import BytesIO


@crew_assignment_bp.route("/export_excel", methods=["GET"])
def export_crew_assignment_excel():
    crew_id = request.args.get("crew_id")
    department_code = request.args.get("department_code")

    crew = CrewDefinition.query.get(crew_id)
    assignments = CrewAssignment.query.filter_by(CrewID=crew_id).all()

    if department_code:
        assignments = [a for a in assignments if a.DepartmentCode == department_code]

    data = []
    for a in assignments:
        profile = HRProfile.query.filter_by(EmployeeID=a.EmployeeID).first()
        full_name = profile.FullName if profile else "Không rõ"
        position = JobPosition.query.get(a.JobPositionID)
        position_name = position.JobPositionName if position else "Chưa rõ"

        data.append(
            {
                "Mã nhân viên": a.EmployeeID,
                "Họ tên": full_name,
                "Chức danh": position_name,
                "Từ ngày": a.StartDate,
                "Đến ngày": a.EndDate,
            }
        )

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="DanhSachNhanVien")
    output.seek(0)

    return send_file(output, download_name="danh_sach_nhan_vien_kip.xlsx", as_attachment=True)


@crew_assignment_bp.route("/export_pdf", methods=["GET"])
def export_crew_assignment_pdf():
    crew_id = request.args.get("crew_id")
    department_code = request.args.get("department_code")

    crew = CrewDefinition.query.get(crew_id)
    assignments = CrewAssignment.query.filter_by(CrewID=crew_id).all()

    if department_code:
        assignments = [a for a in assignments if a.DepartmentCode == department_code]

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", "", 12)

    pdf.cell(200, 10, f"DANH SÁCH NHÂN VIÊN TRONG KÍP {crew.CrewName}", ln=True, align="C")
    pdf.ln(10)

    for a in assignments:
        profile = HRProfile.query.filter_by(EmployeeID=a.EmployeeID).first()
        full_name = profile.FullName if profile else "Không rõ"
        position = JobPosition.query.get(a.JobPositionID)
        position_name = position.JobPositionName if position else "Chưa rõ"
        line = f"{a.EmployeeID} | {full_name} | {position_name}"
        pdf.cell(0, 10, line, ln=True)

    output = BytesIO()
    pdf.output(output)
    output.seek(0)

    return send_file(output, download_name="danh_sach_nhan_vien_kip.pdf", as_attachment=True)
