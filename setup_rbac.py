#!/usr/bin/env python3
"""
Khởi tạo / đồng bộ RBAC: modules, permissions (access+CRUD), vai trò mẫu.
Chạy: python setup_rbac.py
"""
from app import app, db
from models.modules import Module
from models.permissions import Permission
from models.role_permissions import RolePermission
from models.roles import Role
from utils.permission_utils import MODULE_DEFINITIONS, STANDARD_ACTIONS

# (module_code, [actions]) — thiếu action = không gán
ROLE_TEMPLATES = {
    "admin": {
        "*": list(STANDARD_ACTIONS),
    },
    "nhansu": {
        "hr": list(STANDARD_ACTIONS),
        "hr_salary": list(STANDARD_ACTIONS),
        "hr_health": list(STANDARD_ACTIONS),
        "department": list(STANDARD_ACTIONS),
        "attendance": ["access", "read", "create", "update"],
        "crew": list(STANDARD_ACTIONS),
        "procurement": ["access", "read"],
    },
    "hanhchinh": {
        "attendance": ["access", "read", "create", "update"],
        "crew": ["access", "read", "update"],
    },
    "truongphong": {
        "hr": ["access", "read"],
        "department": ["access", "read"],
        "attendance": ["access", "read", "update"],
        "crew": ["access", "read"],
        "hr_health": ["access", "read"],
    },
    "muasam": {
        "procurement": list(STANDARD_ACTIONS),
        "estimation": ["access", "read"],
    },
    "du_toan": {
        "estimation": list(STANDARD_ACTIONS),
        "procurement": ["access", "read"],
    },
    "lanhdao": {
        "hr": ["access", "read"],
        "department": ["access", "read"],
        "attendance": ["access", "read"],
        "crew": ["access", "read"],
        "procurement": ["access", "read"],
        "estimation": ["access", "read"],
    },
    "canbo": {},
}

ACTION_LABELS = {
    "access": "Truy cập phân hệ",
    "read": "Xem",
    "create": "Thêm mới",
    "update": "Cập nhật",
    "delete": "Xóa",
}


def ensure_modules():
    for code, name in MODULE_DEFINITIONS.items():
        mod = Module.query.filter_by(ModuleCode=code).first()
        if not mod:
            mod = Module(ModuleCode=code, ModuleName=name, Description=name)
            db.session.add(mod)
        else:
            mod.ModuleName = name
    db.session.commit()


def ensure_permissions():
    created = 0
    for code in MODULE_DEFINITIONS:
        mod = Module.query.filter_by(ModuleCode=code).first()
        if not mod:
            continue
        for action in STANDARD_ACTIONS:
            perm = Permission.query.filter_by(ModuleID=mod.ModuleID, Action=action).first()
            label = ACTION_LABELS.get(action, action)
            desc = f"{label} — {mod.ModuleName}"
            if not perm:
                perm = Permission(ModuleID=mod.ModuleID, Action=action, Description=desc)
                db.session.add(perm)
                created += 1
            else:
                perm.Description = desc
    db.session.commit()
    return created


def _find_or_create_role(name: str, description: str = "") -> Role:
    role = Role.query.filter(Role.RoleName.ilike(name)).first()
    if not role:
        role = Role(RoleName=name, Description=description or name)
        db.session.add(role)
        db.session.flush()
    return role


def _grant(role: Role, module_code: str, actions: list):
    mod = Module.query.filter_by(ModuleCode=module_code).first()
    if not mod:
        return
    for action in actions:
        perm = Permission.query.filter_by(ModuleID=mod.ModuleID, Action=action).first()
        if not perm:
            continue
        exists = RolePermission.query.filter_by(RoleID=role.RoleID, PermissionID=perm.PermissionID).first()
        if not exists:
            db.session.add(RolePermission(RoleID=role.RoleID, PermissionID=perm.PermissionID))


def backfill_access_for_roles():
    """Role đã có read/create/... thì tự thêm access cùng module."""
    added = 0
    for rp in RolePermission.query.all():
        perm = db.session.get(Permission, rp.PermissionID)
        if not perm or perm.Action not in ("read", "create", "update", "delete"):
            continue
        access_perm = Permission.query.filter_by(ModuleID=perm.ModuleID, Action="access").first()
        if not access_perm:
            continue
        exists = RolePermission.query.filter_by(RoleID=rp.RoleID, PermissionID=access_perm.PermissionID).first()
        if not exists:
            db.session.add(RolePermission(RoleID=rp.RoleID, PermissionID=access_perm.PermissionID))
            added += 1
    db.session.commit()
    return added


def apply_role_templates():
    all_modules = list(MODULE_DEFINITIONS.keys())
    for role_name, spec in ROLE_TEMPLATES.items():
        role = _find_or_create_role(role_name, f"Vai trò mẫu: {role_name}")
        if "*" in spec:
            modules_actions = {m: spec["*"] for m in all_modules}
        else:
            modules_actions = spec
        for mod_code, actions in modules_actions.items():
            _grant(role, mod_code, actions)
    db.session.commit()


def main():
    with app.app_context():
        print("=== CMMS RBAC Setup ===")
        ensure_modules()
        n = ensure_permissions()
        print(f"Permissions synced (+{n} new)")
        apply_role_templates()
        n_access = backfill_access_for_roles()
        print("Role templates applied:", ", ".join(ROLE_TEMPLATES.keys()))
        print(f"Backfill access permissions: +{n_access}")
        print("✅ Hoàn tất. Gán EmployeeRoles cho từng user, sau đó đăng nhập lại.")


if __name__ == "__main__":
    main()
