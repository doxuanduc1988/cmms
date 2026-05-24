from flask import Blueprint, render_template
from flask_login import login_required

from extensions import db
from models.attendance.crew_model import CrewDefinition
from models.crew_assignment import CrewAssignment
from models.hr.department_model import Department
from models.hr.hr_profiles import HRProfile
from models.hr.job_position_model import JobPosition
from utils.permission_utils import check_permission

crew_definitions_bp = Blueprint("crew_definitions", __name__, url_prefix="/crew_definitions")


@crew_definitions_bp.route("/manage", methods=["GET"])
@login_required
@check_permission("crew", "read")
def manage_crew_definitions():
    crews = CrewDefinition.query.order_by(CrewDefinition.CrewID).all()
    return render_template("crew_definitions/crew_list.html", crews=crews)


@crew_definitions_bp.route("/view_employees/<crew_id>", methods=["GET"])
@login_required
@check_permission("crew", "read")
def view_employees(crew_id):
    crew = CrewDefinition.query.filter_by(CrewID=crew_id).first()
    if not crew:
        return "Không tìm thấy kíp!", 404

    assignments = CrewAssignment.query.filter_by(CrewID=crew_id).all()
    employee_ids = [a.EmployeeID for a in assignments]

    employees = HRProfile.query.filter(HRProfile.EmployeeID.in_(employee_ids)).order_by(HRProfile.FullName).all()

    departments = {d.DepartmentCode: d.DepartmentName for d in Department.query.all()}
    positions = {p.JobPositionID: p.JobPositionName for p in JobPosition.query.all()}

    return render_template(
        "crew_definitions/crew_employee_list.html",
        crew=crew,
        employees=employees,
        departments=departments,
        positions=positions,
    )
