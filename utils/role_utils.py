# utils/role_utils.py
from functools import wraps
from flask import session, redirect, url_for, flash, jsonify, request

def require_role(allowed_roles):
    """
    Dekorator pembatasan akses berbasis role.
    Hanya mengizinkan user dengan role tertentu.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            role = session.get("role")
            if not role or role not in allowed_roles:
                msg = f"Akses ditolak. Fitur ini hanya untuk: {', '.join(allowed_roles)}."
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify(success=False, message=msg), 403
                flash(msg, "danger")
                return redirect(url_for("auth.login"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def require_login(f):
    """Dekorator untuk memastikan user sudah login."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Anda harus login terlebih dahulu.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper
