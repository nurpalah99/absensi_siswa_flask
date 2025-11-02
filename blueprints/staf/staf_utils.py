from functools import wraps
from flask import session, redirect, url_for, flash
from ext import db
from models.user_activity import UserActivity

def require_staf(f):
    """Decorator untuk memastikan hanya staf yang bisa mengakses route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'role' not in session or session['role'] != 'staf':
            flash("Akses ditolak. Anda harus login sebagai staf.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

def catat_aktivitas(username, action):
    """Catat setiap aktivitas staf ke tabel UserActivity."""
    try:
        aktivitas = UserActivity(username=username, action=action)
        db.session.add(aktivitas)
        db.session.commit()
    except Exception:
        db.session.rollback()
        

import os
from datetime import datetime

def log_absensi_aksi(nama_staf, pesan):
    """Mencatat aktivitas staf ke file logs/absensi.log"""
    try:
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "absensi.log")

        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        baris = f"[{waktu}] {nama_staf} - {pesan}\n"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(baris)
    except Exception as e:
        print(f"[LOG ERROR] {e}")

