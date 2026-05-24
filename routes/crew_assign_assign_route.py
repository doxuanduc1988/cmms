from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models.hr.hr_profiles import HRProfile
from models.hr.department_model import Department
from models.attendance.crew_model import CrewDefinition
from models.crew_assignment import CrewAssignment
from datetime import datetime, timedelta

assign_bp = Blueprint("crew_assignments_assign", __name__, url_prefix="/crew_assignments")


@assign_bp.route("/assign", methods=["GET", "POST"])
def assign_crew_members():
    crews = CrewDefinition.query.order_by(CrewDefinition.CrewName).all()
    departments = Department.query.order_by(Department.DepartmentName).all()

    selected_crew_id = request.args.get("crew_id") or request.form.get("crew_id")
    selected_department_code = request.args.get("department_code") or request.form.get("department_code")

    if request.method == "POST":
        selected_employee_ids = request.form.getlist("assigned_employee_ids")
        old_assignments = CrewAssignment.query.filter_by(CrewID=selected_crew_id).all()
        old_employee_ids = {a.EmployeeID for a in old_assignments}
        new_employee_ids = set(selected_employee_ids)

        to_remove = old_employee_ids - new_employee_ids
        to_add = new_employee_ids - old_employee_ids

        # Xóa nhân viên bị gỡ
        if to_remove:
            CrewAssignment.query.filter(
                CrewAssignment.CrewID == selected_crew_id, CrewAssignment.EmployeeID.in_(to_remove)
            ).delete(synchronize_session=False)

        # Thêm mới nhân viên
        for emp_id in to_add:
            employee = HRProfile.query.filter_by(EmployeeID=emp_id).first()
            assignment = CrewAssignment(
                CrewID=selected_crew_id,
                EmployeeID=emp_id,
                DepartmentCode=employee.DepartmentCode if employee and employee.DepartmentCode else "WAITCODE",
                JobPositionID=employee.JobPositionID if employee and employee.JobPositionID else 66,
                StartDate=datetime.today().date(),
                EndDate=datetime.today().date() + timedelta(days=365),
            )
            db.session.add(assignment)

        db.session.commit()

        # 🔄 Đồng bộ CrewID vào HRProfiles
        for emp_id in selected_employee_ids:
            profile = HRProfile.query.filter_by(EmployeeID=emp_id).first()
            if profile:
                profile.CrewID = selected_crew_id
        db.session.commit()

        flash("✅ Đã cập nhật nhân viên của kíp!", "success")
        return redirect(
            url_for(
                "crew_assignments_assign.assign_crew_members",
                crew_id=selected_crew_id,
                department_code=selected_department_code,
            )
        )

    employees = []
    assigned_employee_ids = []

    if selected_crew_id:
        assigned_employee_ids = [a.EmployeeID for a in CrewAssignment.query.filter_by(CrewID=selected_crew_id).all()]
        query = HRProfile.query
        if selected_department_code:
            query = query.filter(HRProfile.DepartmentCode == selected_department_code)
        employees = query.order_by(HRProfile.FullName).all()

    return render_template(
        "crew_assignments/assign_duallist.html",
        crews=crews,
        departments=departments,
        selected_crew_id=selected_crew_id,
        selected_department_code=selected_department_code,
        employees=employees,
        assigned_employee_ids=assigned_employee_ids,
    )


"""

with open("/mnt/data/crew_assign_assign_route.py", "w", encoding="utf-8") as f:
    f.write(crew_assign_assign_route_fixed2)

"/mnt/data/crew_assign_assign_route.py"

Mình vừa bị reset môi trường một lần nữa.
Mình sẽ viết lại cực nhanh để gửi file crew_assign_assign_route.py đúng chuẩn cho bạn! 🚀

Chờ mình 1 phút – mình làm lại cực nhanh!
(Mình đang làm ngay.) ✅ ​​






You said:
mình đang chờ bạn!


ChatGPT said:

Analysis errored
python
Always show details

Copy
# Viết lại route assign gán JobPositionID đồng bộ từ HRProfiles
crew_assign_assign_route_fixed = """
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models.hr.hr_profiles import HRProfile
from models.hr.department_model import Department
from models.attendance.crew_model import CrewDefinition
from models.crew_assignment import CrewAssignment
from datetime import datetime, timedelta

assign_bp = Blueprint("crew_assignments_assign", __name__, url_prefix="/crew_assignments")


@assign_bp.route("/assign", methods=["GET", "POST"])
def assign_crew_members():
    crews = CrewDefinition.query.order_by(CrewDefinition.CrewName).all()
    departments = Department.query.order_by(Department.DepartmentName).all()

    selected_crew_id = request.args.get("crew_id") or request.form.get("crew_id")
    selected_department_code = request.args.get("department_code") or request.form.get("department_code")

    if request.method == "POST":
        print("===> POST form keys:", list(request.form.keys()))
        print("===> employee_ids[]:", request.form.getlist("employee_ids"))

        selected_employee_ids = request.form.getlist("assigned_employee_ids")
        old_assignments = CrewAssignment.query.filter_by(CrewID=selected_crew_id).all()
        old_employee_ids = {a.EmployeeID for a in old_assignments}
        new_employee_ids = set(selected_employee_ids)

        to_remove = old_employee_ids - new_employee_ids
        to_add = new_employee_ids - old_employee_ids

        # Xóa nhân viên bị gỡ
        if to_remove:
            CrewAssignment.query.filter(
                CrewAssignment.CrewID == selected_crew_id, CrewAssignment.EmployeeID.in_(to_remove)
            ).delete(synchronize_session=False)

        # Thêm mới nhân viên
        for emp_id in to_add:
            employee = HRProfile.query.filter_by(EmployeeID=emp_id).first()
            assignment = CrewAssignment(
                CrewID=selected_crew_id,
                EmployeeID=emp_id,
                DepartmentCode=employee.DepartmentCode if employee and employee.DepartmentCode else "WAITCODE",
                JobPositionID=employee.JobPositionID if employee and employee.JobPositionID else 66,
                StartDate=datetime.today().date(),
                EndDate=datetime.today().date() + timedelta(days=365),
            )
            db.session.add(assignment)

        db.session.commit()
        flash("✅ Đã cập nhật nhân viên của kíp!", "success")
        return redirect(
            url_for(
                "crew_assignments_assign.assign_crew_members",
                crew_id=selected_crew_id,
                department_code=selected_department_code,
            )
        )

    employees = []
    assigned_employee_ids = []

    if selected_crew_id:
        assigned_employee_ids = [a.EmployeeID for a in CrewAssignment.query.filter_by(CrewID=selected_crew_id).all()]
        query = HRProfile.query
        if selected_department_code:
            query = query.filter(HRProfile.DepartmentCode == selected_department_code)
        employees = query.order_by(HRProfile.FullName).all()

    return render_template(
        "crew_assignments/assign_duallist.html",
        crews=crews,
        departments=departments,
        selected_crew_id=selected_crew_id,
        selected_department_code=selected_department_code,
        employees=employees,
        assigned_employee_ids=assigned_employee_ids,
    )
