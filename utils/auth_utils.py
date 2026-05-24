from functools import wraps
from flask import redirect, url_for, flash, session
from flask import abort


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "employee_id" not in session:
            flash("⚠️ Vui lòng đăng nhập để tiếp tục!", "warning")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapper


def require_approval_roles(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_role = session.get("role", "").lower()
            print("⚠️ ROLE hiện tại:", user_role)
            if user_role == "admin":
                return f(*args, **kwargs)
            if user_role not in [r.lower() for r in roles]:
                abort(403)
            return f(*args, **kwargs)

        return wrapper

    return decorator
