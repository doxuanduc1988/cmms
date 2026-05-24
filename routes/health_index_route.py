# routes/health_index_route.py
from flask import Blueprint, render_template, request
from models.hr.hr_profiles import HRProfile
from utils.permission_utils import check_permission
from sqlalchemy import or_

health_index_bp = Blueprint("health_index", __name__, url_prefix="/health")


@health_index_bp.route("/", methods=["GET"])
@check_permission("hr", "read")
def search_health():
    query = request.args.get("query", "").strip()
    profiles = []
    if query:
        profiles = (
            HRProfile.query.filter(
                or_(HRProfile.EmployeeID.ilike(f"%{query}%"), HRProfile.FullName.ilike(f"%{query}%"))
            )
            .limit(50)
            .all()
        )

    return render_template("health/index.html", query=query, profiles=profiles)
