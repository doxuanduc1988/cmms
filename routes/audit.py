from flask import Blueprint, render_template, session, request
from models.audit_logs import AuditLog
from utils.auth_utils import login_required
from utils.permission_utils import check_permission

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


@audit_bp.route("/logs")
@login_required
@check_permission("system_admin", "read")
def view_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    logs = AuditLog.query.order_by(AuditLog.Timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("audit/logs.html", logs=logs)
