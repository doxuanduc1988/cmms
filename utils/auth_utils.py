from functools import wraps

from flask import abort, flash, redirect, session, url_for

from utils.permission_utils import user_has_any_role, user_is_system_admin


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "employee_id" not in session:
            flash("⚠️ Vui lòng đăng nhập để tiếp tục!", "warning")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapper


def require_approval_roles(*roles):
    """Duyệt chấm công: admin, truongphong, hanhchinh, nhansu (theo session role_names)."""

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if user_is_system_admin() or user_has_any_role(*roles):
                return f(*args, **kwargs)
            abort(403)

        return wrapper

    return decorator
