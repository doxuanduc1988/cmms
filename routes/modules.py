from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models.modules import Module
from models.permissions import Permission
from models.role_permissions import RolePermission
from utils.permission_utils import check_permission

module_bp = Blueprint("module", __name__, url_prefix="/modules")


@module_bp.route("/")
@login_required
@check_permission("system_admin", "read")
def list_modules():
    modules = Module.query.order_by(Module.ModuleCode).all()
    return render_template("modules/list.html", modules=modules)


@module_bp.route("/add", methods=["GET", "POST"])
@login_required
@check_permission("system_admin", "create")
def add_module():
    if request.method == "POST":
        module_code = request.form["ModuleCode"]
        module_name = request.form["ModuleName"]
        description = request.form.get("Description")

        new_module = Module(ModuleCode=module_code, ModuleName=module_name, Description=description)
        db.session.add(new_module)
        db.session.flush()  # để lấy ModuleID

        # ✅ Tạo quyền mặc định dựa trên ModuleID
        default_actions = ["read", "create", "update", "delete"]
        for action in default_actions:
            exists = Permission.query.filter_by(ModuleID=new_module.ModuleID, Action=action).first()
            if not exists:
                db.session.add(Permission(ModuleID=new_module.ModuleID, Action=action))

        db.session.commit()
        flash("✅ Đã thêm module mới và quyền mặc định", "success")
        return redirect(url_for("module.list_modules"))

    return render_template("modules/create.html")


@module_bp.route("/<int:module_id>/edit", methods=["GET", "POST"])
@login_required
@check_permission("system_admin", "update")
def edit_module(module_id):
    module = Module.query.get_or_404(module_id)
    if request.method == "POST":
        module.ModuleCode = request.form["ModuleCode"]
        module.ModuleName = request.form["ModuleName"]
        module.Description = request.form.get("Description")
        db.session.commit()
        flash("Đã cập nhật module.", "success")
        return redirect(url_for("module.list_modules"))
    return render_template("modules/edit.html", module=module)


@module_bp.route("/<int:module_id>/delete", methods=["POST"])
@login_required
@check_permission("system_admin", "delete")
def delete_module(module_id):
    module = Module.query.get_or_404(module_id)

    # ✅ Xoá tất cả quyền của module trước
    permissions = Permission.query.filter_by(ModuleID=module.ModuleID).all()
    for p in permissions:
        db.session.query(RolePermission).filter_by(PermissionID=p.PermissionID).delete()
        db.session.delete(p)

    db.session.delete(module)
    db.session.commit()

    flash("🗑️ Đã xoá module và các quyền liên quan", "info")
    return redirect(url_for("module.list_modules"))
