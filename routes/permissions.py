# ===== routes/permissions.py =====
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models.roles import Role
from models.permissions import Permission
from models.role_permissions import RolePermission
from extensions import db
from utils.permission_utils import check_permission

permission_bp = Blueprint("permission", __name__, url_prefix="/permissions")


@permission_bp.route("/manage", methods=["GET", "POST"])
@login_required
@check_permission("system_admin", "update")
def manage_permissions():
    roles = Role.query.all()
    permissions = Permission.query.all()

    # selected_role_id = request.form.get("role") if request.method == "POST" else None
    selected_role_id = request.form.get("role") if request.method == "POST" else request.args.get("role")

    selected_permissions = []

    if selected_role_id:
        selected_permissions = [rp.PermissionID for rp in RolePermission.query.filter_by(RoleID=selected_role_id).all()]

    if request.method == "POST" and "permissions" in request.form:
        print("🔁 Cập nhật quyền cho RoleID:", selected_role_id)
        print("✔️ Danh sách PermissionID:", request.form.getlist("permissions"))

        RolePermission.query.filter_by(RoleID=selected_role_id).delete()
        for pid in request.form.getlist("permissions"):
            db.session.add(RolePermission(RoleID=selected_role_id, PermissionID=int(pid)))
        db.session.commit()
        flash("✅ Đã cập nhật phân quyền cho vai trò", "success")
        return redirect(url_for("permission.manage_permissions", role=selected_role_id))

    return render_template(
        "permissions/manage.html",
        roles=roles,
        permissions=permissions,
        selected_role_id=int(selected_role_id) if selected_role_id else None,
        selected_permissions=selected_permissions,
    )
