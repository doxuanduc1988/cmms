# routes/roles.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from extensions import db
from models import Role, Module, Permission, RolePermission
from utils.auth_utils import login_required
from utils.permission_utils import check_permission
from utils.audit_utils import log_action

role_bp = Blueprint("role", __name__, url_prefix="/roles")


@role_bp.route("/")
@login_required
@check_permission("system_admin", "read")
def list_roles():
    roles = Role.query.all()
    return render_template("roles/list.html", roles=roles)


@role_bp.route("/sync-modules", methods=["POST"])
@login_required
@check_permission("system_admin", "update")
def sync_modules():
    """
    Tự động quét các hàm view để tìm các module và action được yêu cầu,
    sau đó đăng ký chúng vào CSDL nếu chưa có.
    """
    new_modules_count = 0
    new_perms_count = 0
    
    # Lấy role Admin để gán quyền tự động
    admin_role = Role.query.filter(
        Role.RoleName.ilike('%admin%') | Role.RoleName.ilike('%quản trị%')
    ).first()
    if not admin_role:
        admin_role = Role.query.first()
        
    for endpoint, view_func in current_app.view_functions.items():
        if hasattr(view_func, "_module_code") and hasattr(view_func, "_action"):
            m_code = getattr(view_func, "_module_code")
            # Action có thể list hoặc string
            actions = getattr(view_func, "_action")
            if isinstance(actions, str):
                actions = [actions]
                
            # Đăng ký Module nếu chưa có
            mod = Module.query.filter_by(ModuleCode=m_code).first()
            if not mod:
                # Tạo tên thân thiện cơ bản
                friendly_name = m_code.replace("_", " ").replace(".", " ").title()
                mod = Module(ModuleCode=m_code, ModuleName=friendly_name)
                db.session.add(mod)
                db.session.flush() # Để lấy ModuleID
                new_modules_count += 1
                
            # Đăng ký Permissions nếu chưa có
            for act in actions:
                # Chuẩn hóa tên action
                desc_prefix = {
                    "access": "Truy cập phân hệ",
                    "create": "Thêm mới",
                    "update": "Cập nhật",
                    "delete": "Xóa",
                    "read": "Xem",
                }.get(act, act.capitalize())
                
                perm = Permission.query.filter_by(ModuleID=mod.ModuleID, Action=act).first()
                if not perm:
                    perm = Permission(
                        ModuleID=mod.ModuleID,
                        Action=act,
                        Description=f"{desc_prefix} {mod.ModuleName or mod.ModuleCode}"
                    )
                    db.session.add(perm)
                    db.session.flush()
                    new_perms_count += 1
                    
                    # Tự động gán cho Admin
                    if admin_role:
                        rp = RolePermission(RoleID=admin_role.RoleID, PermissionID=perm.PermissionID)
                        db.session.add(rp)
                        
    db.session.commit()
    flash(f"✅ Đồng bộ hoàn tất! Thêm {new_modules_count} phân hệ và {new_perms_count} quyền mới.", "success")
    return redirect(url_for("role.list_roles"))


@role_bp.route("/edit/<int:role_id>", methods=["GET", "POST"])
@login_required
@check_permission("system_admin", "update")
def edit_role(role_id):
    """
    Cập nhật vai trò theo pattern 2-khối:
      - Khối 1: Giao dịch DB (commit với try/except).
      - Khối 2: Ghi audit log tách riêng; nếu lỗi -> rollback phiên log, chỉ cảnh báo.
    """
    role = Role.query.get_or_404(role_id)
    if request.method == "POST":
        # Lấy dữ liệu form
        role.RoleName = (request.form.get("RoleName") or "").strip()
        role.Description = request.form.get("Description", "")
        if not role.RoleName:
            flash("❌ Tên vai trò không được để trống.", "error")
            return render_template("roles/edit.html", role=role)

        # Lưu sẵn tên để dùng trong logging (tránh lazy load sau commit)
        safe_name = role.RoleName

        # --- KHỐI 1: Giao dịch DB ---
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("⚠️ Không thể cập nhật: Tên vai trò đã tồn tại.", "error")
            return render_template("roles/edit.html", role=role)
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.exception("Lỗi DB khi cập nhật vai trò: %s", e)
            flash("❌ Lỗi hệ thống khi cập nhật vai trò.", "error")
            return render_template("roles/edit.html", role=role)

        # --- KHỐI 2: Ghi audit log (an toàn) ---
        try:
            log_action(
                employee_id=session.get("employee_id"),
                action="update",
                module="roles",
                description=f"Cập nhật vai trò: {safe_name}",
            )
        except Exception as e:
            # ⚠️ Quan trọng: rollback để giải phóng trạng thái phiên sau lỗi log
            db.session.rollback()
            current_app.logger.warning("Ghi audit log thất bại (edit role %s): %s", safe_name, e)

        flash("✅ Đã cập nhật vai trò!", "success")
        return redirect(url_for("role.list_roles"))

    return render_template("roles/edit.html", role=role)


@role_bp.route("/permissions/<int:role_id>", methods=["GET", "POST"])
@login_required
@check_permission("system_admin", "update")
def edit_permissions(role_id):
    """
    Cập nhật quyền theo pattern 2-khối (DB + log).
    """
    role = Role.query.get_or_404(role_id)
    modules = Module.query.all()
    all_permissions = Permission.query.all()
    current_permissions = RolePermission.query.filter_by(RoleID=role.RoleID).all()
    current_ids = [rp.PermissionID for rp in current_permissions]

    if request.method == "POST":
        selected = request.form.getlist("permissions")

        # Lưu sẵn tên để dùng trong logging
        safe_name = role.RoleName

        # --- KHỐI 1: Giao dịch DB ---
        try:
            RolePermission.query.filter_by(RoleID=role.RoleID).delete()
            for pid in selected:
                db.session.add(RolePermission(RoleID=role.RoleID, PermissionID=int(pid)))
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.exception("Lỗi DB khi cập nhật quyền cho vai trò: %s", e)
            flash("❌ Lỗi hệ thống khi cập nhật quyền.", "error")
            return render_template(
                "roles/permissions.html",
                role=role,
                modules=modules,
                all_permissions=all_permissions,
                current_ids=current_ids,
            )

        # --- KHỐI 2: Ghi audit log (an toàn) ---
        try:
            log_action(
                employee_id=session.get("employee_id"),
                action="update",
                module="roles",
                description=f"Gán quyền cho vai trò: {safe_name}",
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.warning("Ghi audit log thất bại (edit permissions %s): %s", safe_name, e)

        flash("✅ Đã cập nhật quyền cho vai trò!", "success")
        return redirect(url_for("role.list_roles"))

    return render_template(
        "roles/permissions.html", role=role, modules=modules, all_permissions=all_permissions, current_ids=current_ids
    )


@role_bp.route("/create", methods=["GET", "POST"])
@login_required
@check_permission("system_admin", "create")
def create_role():
    """
    Tạo vai trò theo pattern 2-khối (DB + log) để tránh 500 nếu log lỗi.
    """
    if request.method == "POST":
        role_name = (request.form.get("RoleName") or "").strip()
        desc = request.form.get("Description", "")
        if not role_name:
            flash("❌ Tên vai trò không được để trống.", "error")
            return render_template("roles/create.html")

        # --- KHỐI 1: Giao dịch DB ---
        try:
            new_role = Role(RoleName=role_name, Description=desc)
            db.session.add(new_role)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("⚠️ Không thể tạo: Tên vai trò đã tồn tại.", "error")
            return render_template("roles/create.html")
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.exception("Lỗi DB khi tạo vai trò: %s", e)
            flash("❌ Lỗi hệ thống khi tạo vai trò.", "error")
            return render_template("roles/create.html")

        # --- KHỐI 2: Ghi audit log (an toàn) ---
        try:
            log_action(
                employee_id=session.get("employee_id"),
                action="create",
                module="roles",
                description=f"Tạo vai trò mới: {role_name}",
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.warning("Ghi audit log thất bại (create role %s): %s", role_name, e)

        flash("✅ Đã thêm vai trò!", "success")
        return redirect(url_for("role.list_roles"))

    return render_template("roles/create.html")


@role_bp.route("/delete/<int:role_id>", methods=["POST"])
@login_required
@check_permission("system_admin", "delete")
def delete_role(role_id: int):
    role = Role.query.get_or_404(role_id)

    # Chặn xoá vai trò hệ thống
    protected_names = {"admin", "administrator", "sysadmin"}
    if (role.RoleName or "").strip().lower() in protected_names:
        flash("⛔ Không thể xoá vai trò hệ thống.", "error")
        return redirect(url_for("role.list_roles"))

    # --- KHỐI 1: CHỈ xử lý xoá + commit ---
    try:
        # Xoá mapping quyền trước để tránh lỗi FK
        RolePermission.query.filter_by(RoleID=role.RoleID).delete(synchronize_session=False)
        db.session.delete(role)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Chỉ hiển thị thông điệp 'đang được sử dụng' khi lỗi phát sinh trong lúc xoá/commit
        flash("⚠️ Không thể xoá vì vai trò đang được sử dụng (đang gán cho tài khoản hoặc ràng buộc khác).", "error")
        return redirect(url_for("role.list_roles"))
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"❌ Lỗi hệ thống khi xoá vai trò: {str(e)}", "error")
        return redirect(url_for("role.list_roles"))

    # --- KHỐI 2: Ghi log (không ảnh hưởng thông báo người dùng) ---
    try:
        log_action(
            employee_id=session.get("employee_id"),
            action="delete",
            module="roles",
            description=f"Xoá vai trò: {role.RoleName}",
        )
    except Exception as e:
        # Không đổi thông báo đã thành công; chỉ ghi log nội bộ
        current_app.logger.warning("Ghi audit log thất bại sau khi xoá vai trò: %s", e)

    # Thông điệp cuối cùng cho người dùng
    flash("✅ Đã xoá vai trò!", "success")
    return redirect(url_for("role.list_roles"))
