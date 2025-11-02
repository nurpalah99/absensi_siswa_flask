# ======================================================
# admin_routes.py (FINAL - Sinkron dengan Dashboard & Login)
# ======================================================
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, session, send_file, current_app
)
from datetime import datetime
from ext import db, bcrypt
from utils.decorators import require_role
from models.user_activity import UserActivity
from models.user import User
from models.siswa import Siswa
from models.absensi import Absensi
from models.pengaturan import Pengaturan
from sqlalchemy import text
import os, random, string
from fpdf import FPDF

# ✅ Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ======================================================
# BEFORE REQUEST → Cek login & role admin
# ======================================================
@admin_bp.before_request
def secure_admin_area():
    allowed_routes = ['admin.static']
    if request.endpoint not in allowed_routes:
        if 'role' not in session or session['role'] != 'admin':
            flash('Akses ditolak. Silakan login terlebih dahulu.', 'danger')
            return redirect(url_for('auth.login'))

# ======================================================
# DASHBOARD ADMIN
# ======================================================
@admin_bp.route('/')
@admin_bp.route('/dashboard', endpoint='dashboard')
@require_role(['admin'])
def dashboard_admin():
    total_siswa = Siswa.query.count()
    total_hadir = Absensi.query.filter_by(status='Hadir').count()
    total_izin = Absensi.query.filter_by(status='Izin').count()
    total_sakit = Absensi.query.filter_by(status='Sakit').count()
    total_terlambat = Absensi.query.filter_by(status='Terlambat').count()

    data_chart = {
        'labels': ['Hadir', 'Izin', 'Sakit', 'Terlambat'],
        'values': [total_hadir, total_izin, total_sakit, total_terlambat]
    }

    return render_template(
        'admin/dashboard_admin.html',
        total_siswa=total_siswa,
        total_hadir=total_hadir,
        total_izin=total_izin,
        total_sakit=total_sakit,
        total_terlambat=total_terlambat,
        data_chart=data_chart
    )

# ======================================================
# RESET TABEL USERS (buat ulang akun admin & staf)
# ======================================================
@admin_bp.route('/reset_user_table', methods=['POST'])
@require_role(['admin'])
def reset_user_table():
    try:
        with current_app.app_context():
            db.session.execute(text("DROP TABLE IF EXISTS users;"))
            db.create_all()

            admin = User(
                nama="Administrator",
                username="admin",
                password=bcrypt.generate_password_hash("admin123").decode('utf-8'),
                role="admin",
                status="Aktif"
            )
            staf = User(
                nama="Staf Absensi",
                username="staf1",
                password=bcrypt.generate_password_hash("staf123").decode('utf-8'),
                role="staf",
                status="Aktif"
            )

            db.session.add_all([admin, staf])
            db.session.commit()

        flash("✅ Tabel User berhasil direset dan akun default dibuat ulang.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Gagal mereset tabel users: {str(e)}", "danger")

    return redirect(url_for('admin.pengaturan_akun'))

# ======================================================
# DATA USER
# ======================================================
@admin_bp.route('/data_user')
@require_role(['admin'])
def data_user():
    users = User.query.order_by(User.id.asc()).all()
    return render_template('admin/data_user.html', users=users)
    
# ======================================================
# DATA SISWA (Sinkron dengan Sidebar)
# ======================================================
@admin_bp.route('/data_siswa')
@require_role(['admin'])
def data_siswa():
    siswa_list = Siswa.query.order_by(Siswa.nama.asc()).all()
    return render_template('admin/data_siswa.html', siswa_list=siswa_list)




# ======================================================
# TAMBAH USER BARU
# ======================================================
@admin_bp.route('/tambah_user', methods=['POST'])
@require_role(['admin'])
def tambah_user():
    nama = request.form.get('nama')
    username = request.form.get('username')
    password = request.form.get('password') or ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    role = request.form.get('role', 'staf')
    nip = request.form.get('nip')
    wali_kelas = request.form.get('wali_kelas')
    status = request.form.get('status', 'aktif')

    if User.query.filter_by(username=username).first():
        flash('❌ Username sudah digunakan.', 'danger')
        return redirect(url_for('admin.pengaturan_akun'))

    try:
        user = User(
            nama=nama,
            username=username,
            role=role,
            nip=nip,
            wali_kelas=wali_kelas,
            status=status,
            password=bcrypt.generate_password_hash(password).decode('utf-8')
        )
        db.session.add(user)
        db.session.commit()

        UserActivity.log(session['nama'], f"Tambah user baru {user.nama} ({user.username})", session['user_id'], 'admin')
        flash(f'✅ User baru "{user.nama}" berhasil ditambahkan (password: {password})', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'❌ Gagal menambahkan user: {e}', 'danger')

    return redirect(url_for('admin.pengaturan_akun'))

# ======================================================
# EDIT USER
# ======================================================
@admin_bp.route('/edit_user/<int:user_id>', methods=['POST'])
@require_role(['admin'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    user.nama = request.form.get('nama')
    user.username = request.form.get('username')
    user.role = request.form.get('role')

    password = request.form.get('password')
    if password:
        user.password = bcrypt.generate_password_hash(password).decode('utf-8')

    db.session.commit()
    UserActivity.log(session['nama'], f"Edit akun {user.nama} ({user.username})", session['user_id'], 'admin')
    flash('✅ Data user berhasil diperbarui.', 'success')
    return redirect(url_for('admin.pengaturan_akun'))

# ======================================================
# RESET PASSWORD USER
# ======================================================
@admin_bp.route('/reset_password_user/<int:user_id>')
@require_role(['admin'])
def reset_password_user(user_id):
    user = User.query.get_or_404(user_id)
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()

    UserActivity.log(session['nama'], f"Reset password {user.username}", session['user_id'], 'admin')
    flash(f"✅ Password untuk {user.nama} berhasil direset.", "success")
    return redirect(url_for('admin.pengaturan_akun'))

# ======================================================
# GENERATE PASSWORD UNTUK SEMUA USER (Kecuali Admin)
# ======================================================
@admin_bp.route('/generate_passwords')
@require_role(['admin'])
def generate_passwords():
    users = User.query.all()
    changed = 0
    for u in users:
        if u.role == 'admin':
            continue
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        u.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        changed += 1

    db.session.commit()
    UserActivity.log(session.get('nama', 'system'), f"Generate password untuk {changed} user non-admin", session.get('user_id'), 'admin')
    flash(f"✅ Password untuk {changed} user non-admin telah digenerate ulang.", "success")
    return redirect(url_for('admin.pengaturan_akun'))

# ======================================================
# PENGATURAN AKUN ADMIN
# ======================================================
@admin_bp.route('/pengaturan_akun', methods=['GET', 'POST'])
@require_role(['admin'])
def pengaturan_akun():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    semua_user = User.query.all()

    if request.method == 'POST' and request.form.get('form_type') == 'update_profile':
        nama = request.form['nama']
        username = request.form['username']
        password = request.form.get('password')
        foto = request.files.get('foto')

        user.nama = nama
        user.username = username
        if password:
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')

        if foto and foto.filename != '':
            os.makedirs('static/uploads', exist_ok=True)
            filename = f"user_{user.id}.jpg"
            foto.save(f"static/uploads/{filename}")
            user.foto = filename

        db.session.commit()
        UserActivity.log(session['nama'], "Perbarui profil admin", session['user_id'], 'admin')
        flash('✅ Profil berhasil diperbarui.', 'success')
        return redirect(url_for('admin.pengaturan_akun'))

    return render_template('admin/pengaturan_akun.html', user=user, semua_user=semua_user)

# ======================================================
# PENGATURAN UMUM SEKOLAH
# ======================================================
@admin_bp.route("/pengaturan_umum", methods=["GET", "POST"])
@require_role(["admin"])
def pengaturan_umum():
    hari_list = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]

    if request.method == "POST":
        try:
            for key in ["jam_masuk", "jam_pulang", "jam_awal_pulang", "kepala_sekolah", "operator"]:
                nilai = request.form.get(key)
                if nilai:
                    item = Pengaturan.query.filter_by(kunci=key).first()
                    if item:
                        item.nilai = nilai
                    else:
                        db.session.add(Pengaturan(kunci=key, nilai=nilai))

            for hari in hari_list:
                field = f"jam_pulang_{hari.lower()}"
                jam = request.form.get(field)
                if jam:
                    item = Pengaturan.query.filter_by(kunci=field).first()
                    if item:
                        item.nilai = jam
                    else:
                        db.session.add(Pengaturan(kunci=field, nilai=jam))

            db.session.commit()
            flash("✅ Pengaturan berhasil disimpan.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Gagal menyimpan pengaturan: {e}", "danger")

        return redirect(url_for("admin.pengaturan_umum"))

    data_pengaturan = {p.kunci: p.nilai for p in Pengaturan.query.all()}
    data_per_hari = {hari: data_pengaturan.get(f"jam_pulang_{hari.lower()}", "") for hari in hari_list}

    return render_template("admin/pengaturan_umum.html", data=data_pengaturan, data_per_hari=data_per_hari)






# ======================================================
# PLACEHOLDER MENU TAMBAHAN DARI SIDEBAR
# ======================================================
@admin_bp.route('/laporan_absensi')
@require_role(['admin'])
def laporan_absensi():
    return render_template('admin/laporan_absensi.html')

@admin_bp.route('/import_user')
@require_role(['admin'])
def import_user():
    return render_template('admin/import_user.html')

@admin_bp.route('/log_aktivitas')
@require_role(['admin'])
def log_aktivitas():
    logs = UserActivity.query.order_by(UserActivity.timestamp.desc()).limit(100).all()
    return render_template('admin/log_aktivitas.html', logs=logs)

@admin_bp.route('/reset_data')
@require_role(['admin'])
def reset_data():
    flash("⚠️ Fitur reset data belum diaktifkan.", "warning")
    return redirect(url_for('admin.dashboard_admin'))
