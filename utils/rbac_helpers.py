"""Hỗ trợ chuẩn hóa danh sách PermissionID khi lưu vai trò."""
from models.permissions import Permission

ACTION_ORDER = ("access", "read", "create", "update", "delete")


def expand_permission_ids_with_access(selected_ids: list) -> list[int]:
    """Nếu có read/create/update/delete trên module thì tự thêm access."""
    if not selected_ids:
        return []
    selected = {int(x) for x in selected_ids}
    perms = Permission.query.filter(Permission.PermissionID.in_(selected)).all()
    module_ids = {p.ModuleID for p in perms}
    for mid in module_ids:
        access = Permission.query.filter_by(ModuleID=mid, Action="access").first()
        if access:
            selected.add(access.PermissionID)
    return sorted(selected)


def permissions_by_module_action(all_permissions):
    """Map (ModuleID, action) -> Permission (một bản ghi)."""
    out = {}
    for p in all_permissions:
        key = (p.ModuleID, p.Action)
        if key not in out:
            out[key] = p
    return out
