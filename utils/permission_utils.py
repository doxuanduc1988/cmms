from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from models import RolePermission, Permission, Module
from extensions import db
from pathlib import Path
from flask_login import current_user


def check_permission(module_code, action):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("⚠️ Bạn cần đăng nhập để tiếp tục!", "warning")
                return redirect(url_for("auth.login"))

            # Bỏ qua kiểm tra phân quyền đối với các hành động xem (trừ system_admin)
            if action in ["read", "view", "list"] and module_code != "system_admin":
                return view_func(*args, **kwargs)

            # Lấy tất cả RoleID của user
            role_ids = [r.RoleID for r in current_user.roles]
            if not role_ids:
                flash("⛔ Bạn chưa được gán vai trò hệ thống!", "error")
                return redirect(url_for("dashboard"))

            # Truy vấn permission hợp lệ (Bất kỳ vai trò nào có quyền đều OK)
            permission = (
                db.session.query(Permission)
                .join(Module, Permission.ModuleID == Module.ModuleID)
                .join(RolePermission, Permission.PermissionID == RolePermission.PermissionID)
                .filter(Module.ModuleCode == module_code, Permission.Action == action, RolePermission.RoleID.in_(role_ids))
                .first()
            )

            if permission:
                return view_func(*args, **kwargs)
            else:
                is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
                if is_ajax:
                    return jsonify({"error": "Bạn không có quyền thực hiện hành động này!", "status": "error"}), 403
                flash("⛔ Bạn không có quyền thực hiện hành động này!", "error")
                return redirect(request.referrer or url_for("dashboard"))

        wrapped_view._module_code = module_code
        wrapped_view._action = action
        return wrapped_view

    return decorator


def has_permission(user, module_code, action):
    if not user or not user.is_authenticated:
        return False

    # Bỏ qua kiểm tra phân quyền đối với các hành động xem (trừ system_admin)
    if action in ["read", "view", "list"] and module_code != "system_admin":
        return True

    role_ids = [r.RoleID for r in user.roles]
    if not role_ids:
        return False

    permission = (
        db.session.query(Permission)
        .join(Module, Permission.ModuleID == Module.ModuleID)
        .join(RolePermission, Permission.PermissionID == RolePermission.PermissionID)
        .filter(Module.ModuleCode == module_code, Permission.Action == action, RolePermission.RoleID.in_(role_ids))
        .first()
    )

    return permission is not None


def has_permission_view(module_code, action="read"):
    return has_permission(current_user, module_code, action)
