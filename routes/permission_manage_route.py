from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models.permissions import Permission
from utils.permission_utils import check_permission

permission_manage_bp = Blueprint("permission_manage", __name__, url_prefix="/permission-manage")


@permission_manage_bp.route("/")
@check_permission("system_admin", "read")
def permission_list():
    permissions = Permission.query.order_by(Permission.ModuleCode, Permission.Action).all()
    return render_template("permissions/permission_list.html", permissions=permissions)


@permission_manage_bp.route("/create", methods=["GET", "POST"])
@check_permission("system_admin", "create")
def permission_create():
    if request.method == "POST":
        module_code = request.form.get("ModuleCode").strip()
        actions = request.form.getlist("actions")

        created = 0
        for action in actions:
            exists = Permission.query.filter_by(ModuleCode=module_code, Action=action).first()
            if not exists:
                db.session.add(Permission(ModuleCode=module_code, Action=action))
                created += 1
        db.session.commit()
        flash(f"Đã thêm {created} quyền cho module {module_code}.", "success")
        return redirect(url_for("permission_manage.permission_list"))

    return render_template("permissions/permission_form.html")
