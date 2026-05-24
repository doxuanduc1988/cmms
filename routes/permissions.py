# ===== routes/permissions.py =====
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models.roles import Role
from models.permissions import Permission
from models.role_permissions import RolePermission
from extensions import db
from utils.permission_utils import check_permission
from utils.rbac_helpers import expand_permission_ids_with_access
from utils.rbac_helpers import permissions_by_module_action

permission_bp = Blueprint("permission", __name__, url_prefix="/permissions")


@permission_bp.route("/manage", methods=["GET", "POST"])
@login_required
@check_permission("system_admin", "update")
def manage_permissions():
    roles = Role.query.all()
    from sqlalchemy.orm import joinedload

    permissions = Permission.query.options(joinedload(Permission.module)).order_by(Permission.ModuleID, Permission.Action).all()

    # selected_role_id = request.form.get("role") if request.method == "POST" else None
    selected_role_id = request.form.get("role") if request.method == "POST" else request.args.get("role")
    selected_role_id = int(selected_role_id) if selected_role_id else None

    selected_permissions = []
    if selected_role_id:
        selected_permissions = [rp.PermissionID for rp in RolePermission.query.filter_by(RoleID=selected_role_id).all()]

    if request.method == "POST" and selected_role_id and "permissions" in request.form:
        expanded = expand_permission_ids_with_access(request.form.getlist("permissions"))
        RolePermission.query.filter_by(RoleID=selected_role_id).delete()
        for pid in expanded:
            db.session.add(RolePermission(RoleID=selected_role_id, PermissionID=int(pid)))
        db.session.commit()
        flash("✅ Đã cập nhật phân quyền cho vai trò", "success")
        return redirect(url_for("permission.manage_permissions", role=selected_role_id))

    pmap = permissions_by_module_action(permissions)
    permissions_grouped = []
    seen_modules = []
    for p in permissions:
        code = p.module.ModuleCode if p.module else "?"
        if code not in seen_modules:
            seen_modules.append(code)
    for code in seen_modules:
        module_perms = sorted(
            [pmap[k] for k in pmap if pmap[k].module and pmap[k].module.ModuleCode == code],
            key=lambda x: ["access", "read", "create", "update", "delete"].index(x.Action)
            if x.Action in ("access", "read", "create", "update", "delete")
            else 99,
        )
        permissions_grouped.append((code, module_perms))

    return render_template(
        "permissions/manage.html",
        roles=roles,
        permissions_grouped=permissions_grouped,
        selected_role_id=selected_role_id,
        selected_permissions=selected_permissions,
    )
