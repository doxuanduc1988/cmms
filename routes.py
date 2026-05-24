from flask import Blueprint, render_template
from models import db, Department

department_bp = Blueprint("department_bp", __name__)


@department_bp.route("/departments")
def list_departments():
    departments = Department.query.all()
    return render_template("departments.html", departments=departments)
