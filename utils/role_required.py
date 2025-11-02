from functools import wraps
from flask import session, redirect, url_for, flash, jsonify, request

def require_role(allowed_roles):
    """
    Dekorator pembatasan akses berbasis role.
    Hanya mengizinkan user dengan role tertentu untuk menjalankan fungsi.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            role = session.get("role")

            # Jika belum login
            if not role:
                flash("Silakan login terlebih dahulu.", "warning")
                return redirect(url_for("auth.login"))

            # Jika role tidak diizinkan
            if role not in allowed_roles:
                msg = f"Akses ditolak. Fitur ini hanya untuk: {', '.join(allowed_roles)}."
                # Jika request dari AJAX (JSON)
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify(success=False, message=msg), 403

                flash(msg, "danger")

                # Arahkan sesuai role login
                if role == "admin":
                    return redirect(url_for("admin.dashboard_admin"))
                elif role == "walikelas":
                    return redirect(url_for("walikelas.dashboard_wali"))
                elif role == "staf":
                    return redirect(url_for("staf_main.dashboard_staf"))
                else:
                    return redirect(url_for("auth.login"))

            # Role diizinkan → jalankan fungsi
            return f(*args, **kwargs)
        return wrapper
    return decorator
    
# Kompatibilitas untuk blueprint lama
role_required = require_role

