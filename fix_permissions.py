from app import app, db
from models.modules import Module
from models.permissions import Permission
from models.role_permissions import RolePermission

with app.app_context():
    # Bước 1: Xoá tất cả các permissions rác hoặc thừa (nếu muốn làm sạch, nhưng cẩn thận tránh mất role_permissions)
    # Tốt hơn là chuẩn hóa thay vì xóa.
    
    # Định nghĩa các action chuẩn và tên mô tả
    STANDARD_ACTIONS = {
        "access": "Truy cập phân hệ",
        "read": "Xem",
        "create": "Thêm mới",
        "update": "Cập nhật",
        "delete": "Xóa",
    }

    # Đổi tên tất cả 'edit' thành 'update'
    permissions_to_update = Permission.query.filter_by(Action="edit").all()
    for p in permissions_to_update:
        # Check if "update" already exists
        existing_update = Permission.query.filter_by(ModuleID=p.ModuleID, Action="update").first()
        if existing_update:
            # Chuyển role_permissions từ 'edit' sang 'update'
            rps = RolePermission.query.filter_by(PermissionID=p.PermissionID).all()
            for rp in rps:
                # Tránh duplicate
                if not RolePermission.query.filter_by(RoleID=rp.RoleID, PermissionID=existing_update.PermissionID).first():
                    rp.PermissionID = existing_update.PermissionID
                else:
                    db.session.delete(rp)
            db.session.delete(p)
        else:
            p.Action = "update"
            
    db.session.commit()

    # Chuẩn hóa Description cho tất cả Permission
    modules = Module.query.all()
    for mod in modules:
        for action, desc_prefix in STANDARD_ACTIONS.items():
            # Kiểm tra xem permission đã tồn tại chưa
            perm = Permission.query.filter_by(ModuleID=mod.ModuleID, Action=action).first()
            if not perm:
                # Tạo mới nếu chưa có
                perm = Permission(
                    ModuleID=mod.ModuleID,
                    Action=action,
                    Description=f"{desc_prefix} {mod.ModuleName}"
                )
                db.session.add(perm)
            else:
                # Cập nhật Description cho chuẩn và đẹp
                perm.Description = f"{desc_prefix} {mod.ModuleName}"
                
    db.session.commit()
    print("✅ Đã chuẩn hóa Permissions và Modules thành công!")

    # In ra để xem lại
    print("\n--- PERMISSIONS SAU KHI CHUẨN HÓA ---")
    all_perms = Permission.query.order_by(Permission.ModuleID, Permission.Action).all()
    for p in all_perms:
        m_code = p.module.ModuleCode if p.module else 'None'
        print(f"[{p.PermissionID}] {m_code} - Action: {p.Action} - Description: {p.Description}")
