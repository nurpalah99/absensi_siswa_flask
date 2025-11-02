from functools import wraps
from flask import session, redirect, url_for, flash

def require_role(roles):
    """
    Dekorator untuk membatasi akses berdasarkan role pengguna.
    roles: list role yang diizinkan, contoh ['admin', 'staf', 'guru']
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_role = session.get('role')
            if not user_role or user_role not in roles:
                flash("Anda tidak memiliki izin untuk mengakses halaman ini.", "danger")
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return wrapper
    return decorator

# utils/decorators.py
from functools import wraps
from flask import session, redirect, url_for, flash

def login_required_staf(f):
    """Pastikan hanya staf yang bisa mengakses halaman tertentu."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('role')
        if role != 'staf':
            flash("Silakan login terlebih dahulu sebagai staf.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
