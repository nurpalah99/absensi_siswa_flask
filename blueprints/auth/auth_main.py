from flask import render_template, request, redirect, url_for, session, flash
from models.user import User
from models.user_activity import UserActivity
from ext import db, bcrypt
from utils.logger import log_info, log_warning, log_error
from . import auth_bp
from datetime import timedelta

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Jika sudah login, arahkan langsung ke dashboard
    if "role" in session:
        role = session["role"]
        if role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif role == "staf":
            return redirect(url_for("staf.dashboard"))
        elif role == "walikelas":
            return redirect(url_for("walikelas.dashboard"))
        elif role == "operator":
            return redirect(url_for("operator.dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            user = User.query.filter_by(username=username).first()
        except Exception as e:
            log_error(f"Kesalahan saat mengakses database: {e}")
            flash("Kesalahan sistem. Hubungi admin.", "danger")
            return redirect(url_for("auth.login"))

        if not user:
            flash("Username tidak ditemukan", "danger")
            log_warning(f"Login gagal: username {username} tidak ditemukan")
            return redirect(url_for("auth.login"))

        # Verifikasi password
        try:
            if not bcrypt.check_password_hash(user.password, password):
                flash("Password salah", "danger")
                log_warning(f"Login gagal: password salah untuk {username}")
                return redirect(url_for("auth.login"))
        except Exception:
            # fallback plaintext lama
            if user.password == password:
                user.set_password(password)
                db.session.commit()
                log_info(f"Password user {username} diupgrade ke bcrypt.")
            else:
                flash("Password salah", "danger")
                return redirect(url_for("auth.login"))

        if user.status.lower() != "aktif":
            flash("Akun Anda tidak aktif. Hubungi admin.", "warning")
            log_warning(f"Login ditolak: akun {username} tidak aktif")
            return redirect(url_for("auth.login"))

        # Simpan sesi
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role
        session["nama"] = user.nama
        session.permanent = True
        auth_bp.permanent_session_lifetime = timedelta(minutes=60)

        user.update_last_login()
        db.session.commit()

        UserActivity.log(
            username=user.username,
            action=f"Login berhasil sebagai {user.role}",
            user_id=user.id,
            role=user.role,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
        )

        log_info(f"User {user.username} login sebagai {user.role}")

        if user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif user.role == "staf":
            return redirect(url_for("staf.dashboard"))
        elif user.role == "walikelas":
            return redirect(url_for("walikelas.dashboard"))
        elif user.role == "operator":
            return redirect(url_for("operator.dashboard"))
        else:
            flash("Role tidak dikenali, hubungi administrator.", "warning")
            return redirect(url_for("auth.login"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    username = session.get("username", "tidak diketahui")
    role = session.get("role", "-")
    user_id = session.get("user_id")

    UserActivity.log(
        username=username,
        action="Logout dari sistem",
        user_id=user_id,
        role=role,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
    )

    log_info(f"User {username} logout.")
    session.clear()
    flash("Anda telah logout.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/")
def index_redirect():
    """Redirect otomatis ke halaman login."""
    return redirect(url_for("auth.login"))
