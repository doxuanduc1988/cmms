"""
RBAC 3 lớp: access (vào phân hệ) → action (CRUD) → data scope (all/department/self).
Quyền được cache trong session sau khi đăng nhập.
"""
from functools import wraps

from flask import flash, jsonify, redirect, request, session, url_for
from flask_login import current_user

from extensions import db
from models import Module, Permission, RolePermission

# Chuẩn hóa alias action
ACTION_ALIASES = {"view": "read", "list": "read", "edit": "update"}

STANDARD_ACTIONS = ("access", "read", "create", "update", "delete")

# Phạm vi dữ liệu theo tên vai trò (ưu tiên: all > department > self)
SCOPE_PRIORITY = {"self": 0, "department": 1, "all": 2}

ROLE_SCOPE_HINTS = {
    "admin": "all",
    "quản trị": "all",
    "administrator": "all",
    "nhansu": "all",
    "nhân sự": "all",
    "hanhchinh": "all",
    "hành chính": "all",
    "muasam": "all",
    "mua sắm": "all",
    "du_toan": "all",
    "dự toán": "all",
    "lanhdao": "all",
    "lãnh đạo": "all",
    "truongphong": "department",
    "trưởng phòng": "department",
    "canbo": "self",
    "cán bộ": "self",
}

# Module code → tên hiển thị (đồng bộ DB)
MODULE_DEFINITIONS = {
    "system_admin": "Quản trị hệ thống",
    "hr": "Nhân sự & Hồ sơ",
    "hr_salary": "Lương & phụ cấp",
    "hr_health": "Sức khỏe nhân sự",
    "department": "Phòng ban & tổ chức",
    "attendance": "Chấm công",
    "crew": "Ca / Tổ",
    "procurement": "Mua sắm & đấu thầu",
    "estimation": "Dự toán chi phí",
}


def _perm_key(module_code: str, action: str) -> str:
    return f"{module_code}:{action}"


def _normalize_action(action: str) -> str:
    return ACTION_ALIASES.get(action, action)


def _session_perms() -> set:
    return set(session.get("permissions") or [])


def _load_permissions_from_db(user) -> set:
    role_ids = [r.RoleID for r in user.roles]
    if not role_ids:
        return set()
    rows = (
        db.session.query(Module.ModuleCode, Permission.Action)
        .join(Permission, Permission.ModuleID == Module.ModuleID)
        .join(RolePermission, RolePermission.PermissionID == Permission.PermissionID)
        .filter(RolePermission.RoleID.in_(role_ids))
        .all()
    )
    return {_perm_key(m, a) for m, a in rows}


def refresh_session_permissions(user) -> None:
    """Gọi sau login_user() để cache quyền và vai trò."""
    user_roles = list(user.roles)
    role_names = [r.RoleName for r in user_roles]
    role_names_lower = [n.lower() for n in role_names]

    session["role_ids"] = [r.RoleID for r in user_roles]
    session["role_names"] = role_names
    session["role_names_lower"] = role_names_lower
    session["role_name"] = ", ".join(role_names) if role_names else "Chưa phân vai"
    session["role_id"] = user_roles[0].RoleID if user_roles else None
    session["role"] = role_names_lower[0] if role_names_lower else ""

    perms = _load_permissions_from_db(user)
    session["permissions"] = sorted(perms)
    session["data_scopes"] = _compute_module_scopes(role_names_lower)


def clear_session_permissions() -> None:
    for key in ("permissions", "role_ids", "role_names", "role_names_lower", "data_scopes"):
        session.pop(key, None)


def _compute_module_scopes(role_names_lower: list) -> dict:
    """Phạm vi mặc định theo vai trò (có thể mở rộng per-module sau)."""
    best = "self"
    for name in role_names_lower:
        for hint, scope in ROLE_SCOPE_HINTS.items():
            if hint in name:
                if SCOPE_PRIORITY[scope] > SCOPE_PRIORITY[best]:
                    best = scope
    return {
        "hr": best,
        "hr_salary": "all" if best == "all" else "department" if best == "department" else "self",
        "hr_health": best,
        "attendance": best,
        "department": best,
        "crew": best,
        "procurement": best,
        "estimation": best,
        "system_admin": "all",
    }


def user_has_permission(user, module_code: str, action: str) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    action = _normalize_action(action)
    key = _perm_key(module_code, action)
    cached = _session_perms()
    if cached:
        return key in cached
    return key in _load_permissions_from_db(user)


def has_module_access(user, module_code: str) -> bool:
    """Được phép vào phân hệ (access hoặc bất kỳ quyền nào trên module)."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    prefix = f"{module_code}:"
    cached = _session_perms()
    if cached:
        if _perm_key(module_code, "access") in cached:
            return True
        return any(p.startswith(prefix) for p in cached)
    role_ids = [r.RoleID for r in user.roles]
    if not role_ids:
        return False
    return (
        db.session.query(Permission.PermissionID)
        .join(Module, Permission.ModuleID == Module.ModuleID)
        .join(RolePermission, RolePermission.PermissionID == Permission.PermissionID)
        .filter(Module.ModuleCode == module_code, RolePermission.RoleID.in_(role_ids))
        .first()
        is not None
    )


def has_permission(user, module_code: str, action: str) -> bool:
    action = _normalize_action(action)
    if action == "access":
        return user_has_permission(user, module_code, "access")
    return user_has_permission(user, module_code, action)


def has_permission_view(module_code: str, action: str = "read") -> bool:
    return has_permission(current_user, module_code, action)


def has_module_access_view(module_code: str) -> bool:
    return has_module_access(current_user, module_code)


def user_is_system_admin(user=None) -> bool:
    user = user or current_user
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if has_module_access(user, "system_admin"):
        return True
    names = session.get("role_names_lower") or []
    return any("admin" in n or "quản trị" in n for n in names)


def get_data_scope(module_code: str) -> str:
    scopes = session.get("data_scopes") or {}
    if user_is_system_admin():
        return "all"
    return scopes.get(module_code, "all")


def apply_department_scope(query, model, module_code: str = "hr", dept_column_name: str = "DepartmentCode"):
    """Lọc query theo phòng ban / cá nhân khi scope không phải all."""
    scope = get_data_scope(module_code)
    if scope == "all" or user_is_system_admin():
        return query
    if scope == "department":
        dept = session.get("department_code")
        if dept and hasattr(model, dept_column_name):
            col = getattr(model, dept_column_name)
            return query.filter(col == dept)
    if scope == "self":
        emp_id = session.get("employee_id")
        if emp_id and hasattr(model, "EmployeeID"):
            return query.filter(model.EmployeeID == emp_id)
    return query


def user_has_any_role(*role_hints: str) -> bool:
    names = session.get("role_names_lower") or []
    hints = [h.lower() for h in role_hints]
    if user_is_system_admin():
        return True
    return any(any(hint in n for hint in hints) for n in names)


def check_permission(module_code, action):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("⚠️ Bạn cần đăng nhập để tiếp tục!", "warning")
                return redirect(url_for("auth.login"))

            act = _normalize_action(action)

            if act == "access":
                allowed = has_module_access(current_user, module_code)
            else:
                allowed = user_has_permission(current_user, module_code, act)
                # read/create/update/delete yêu cầu đã có quyền vào phân hệ
                if allowed and act != "access" and module_code != "system_admin":
                    if not has_module_access(current_user, module_code):
                        allowed = False

            if not allowed:
                role_ids = session.get("role_ids") or [r.RoleID for r in current_user.roles]
                if not role_ids:
                    flash("⛔ Bạn chưa được gán vai trò hệ thống!", "error")
                    return redirect(url_for("dashboard.dashboard"))
                is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
                if is_ajax:
                    return jsonify({"error": "Bạn không có quyền thực hiện hành động này!", "status": "error"}), 403
                flash("⛔ Bạn không có quyền thực hiện hành động này!", "error")
                return redirect(request.referrer or url_for("dashboard.dashboard"))

            return view_func(*args, **kwargs)

        wrapped_view._module_code = module_code
        wrapped_view._action = action
        return wrapped_view

    return decorator
