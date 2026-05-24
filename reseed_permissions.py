from app import app, db
from models.modules import Module
from models.permissions import Permission
from models.role_permissions import RolePermission
from models.roles import Role

with app.app_context():
    print("Bắt đầu khởi tạo lại phân quyền...")
    
    # Xoá toàn bộ mapping phân quyền hiện tại
    print("Xóa RolePermissions...")
    db.session.query(RolePermission).delete()
    
    # Xóa toàn bộ permissions
    print("Xóa Permissions...")
    db.session.query(Permission).delete()
    db.session.commit()

    # Tìm Role Admin (Giả định RoleName là 'admin', 'administrator' hoặc RoleID=1)
    admin_role = Role.query.filter(
        Role.RoleName.ilike('%admin%') | Role.RoleName.ilike('%quản trị%')
    ).first()
    
    if not admin_role:
        admin_role = Role.query.first()
        print(f"⚠️ Không tìm thấy Role 'admin', sử dụng Role: {admin_role.RoleName}")
    else:
        print(f"✅ Tìm thấy Admin Role: {admin_role.RoleName} (ID: {admin_role.RoleID})")

    # Các quyền tiêu chuẩn
    STANDARD_ACTIONS = {
        "create": "Thêm mới",
        "update": "Cập nhật",
        "delete": "Xóa"
    }

    modules = Module.query.all()
    created_perms_count = 0
    
    for mod in modules:
        # audit_logs thường chỉ cho admin xem (đã xử lý logic bỏ qua 'read' trừ audit_logs)
        # Tuy nhiên, nếu cần tạo quyền read cho audit_logs thì thêm:
        if mod.ModuleCode == 'audit_logs':
            perm_read = Permission(
                ModuleID=mod.ModuleID,
                Action='read',
                Description=f"Xem {mod.ModuleName}"
            )
            db.session.add(perm_read)
            db.session.flush()
            rp = RolePermission(RoleID=admin_role.RoleID, PermissionID=perm_read.PermissionID)
            db.session.add(rp)

        # Tạo các quyền chuẩn (create, update, delete) cho tất cả các module
        for action, desc_prefix in STANDARD_ACTIONS.items():
            perm = Permission(
                ModuleID=mod.ModuleID,
                Action=action,
                Description=f"{desc_prefix} {mod.ModuleName}"
            )
            db.session.add(perm)
            db.session.flush() # Lấy được PermissionID
            
            # Gán quyền này cho Admin Role
            rp = RolePermission(RoleID=admin_role.RoleID, PermissionID=perm.PermissionID)
            db.session.add(rp)
            
            created_perms_count += 1

    try:
        db.session.commit()
        print(f"✅ Đã tạo thành công {created_perms_count} quyền chuẩn và gán cho {admin_role.RoleName}!")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Có lỗi xảy ra khi lưu: {e}")
