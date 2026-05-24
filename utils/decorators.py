from functools import wraps
from flask import session, redirect, url_for, flash, request
from utils.auth_utils import login_required


def role_required(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            role = session.get("role_name", "")
            if role not in required_roles:
                return redirect(request.referrer or url_for("dashboard"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator
