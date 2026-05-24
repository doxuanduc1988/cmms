# Tạo route Flask và giao diện dual listbox chọn nhân viên cho một kíp
# - Route: /crew_assignments/manage
# - Giao diện có ô tìm kiếm nhân viên chưa gán

from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models.hr.hr_profiles import HRProfile
from models.attendance.crew_model import CrewDefinition
from models.crew_assignment import CrewAssignment

crew_assignment_bp = Blueprint("crew_assignment", __name__, url_prefix="/crew_assignments")


@crew_assignment_bp.route("/manage", methods=["GET", "POST"])
def manage_crew_assignments():
    crews = CrewDefinition.query.order_by(CrewDefinition.CrewName).all()
    selected_crew_id = request.args.get("crew_id") or None

    if request.method == "POST":
        selected_crew_id = request.form.get("crew_id")
        selected_employee_ids = request.form.getlist("assigned_employee_ids")

        if selected_crew_id:
            # Xóa danh sách cũ
            CrewAssignment.query.filter_by(CrewID=selected_crew_id).delete()
            db.session.commit()

            # Thêm mới
            for emp_id in selected_employee_ids:
                assignment = CrewAssignment(CrewID=selected_crew_id, EmployeeID=emp_id)
                db.session.add(assignment)

            db.session.commit()

            # 🔄 Đồng bộ CrewID vào HRProfiles
            for emp_id in selected_employee_ids:
                profile = HRProfile.query.filter_by(EmployeeID=emp_id).first()
                if profile:
                    profile.CrewID = selected_crew_id
            db.session.commit()
            flash("✅ Đã cập nhật danh sách nhân viên cho kíp!", "success")
            return redirect(url_for("crew_assignment.manage_crew_assignments", crew_id=selected_crew_id))

    employees = []
    assigned_employee_ids = []

    if selected_crew_id:
        # Lấy nhân viên đã gán kíp
        assigned_employee_ids = [a.EmployeeID for a in CrewAssignment.query.filter_by(CrewID=selected_crew_id).all()]

        # Lấy tất cả nhân viên
        employees = HRProfile.query.order_by(HRProfile.FullName).all()

    return render_template(
        "crew_assignments/crew_assignment_manage.html",
        crews=crews,
        selected_crew_id=selected_crew_id,
        employees=employees,
        assigned_employee_ids=assigned_employee_ids,
    )
