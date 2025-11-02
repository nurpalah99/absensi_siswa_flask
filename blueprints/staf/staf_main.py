from flask import Blueprint, render_template, request, session, jsonify
from datetime import datetime
from models.absensi import Absensi
from models.siswa import Siswa
from models.pengaturan import Pengaturan
from utils.decorators import login_required_staf
from ext import db
from .staf_utils import catat_aktivitas

# ✅ INISIALISASI BLUEPRINT STAF
staf_bp = Blueprint('staf', __name__, url_prefix='/staf')

# ==================== DASHBOARD ====================
@staf_bp.route('/')
@staf_bp.route('/dashboard', endpoint='dashboard')
def dashboard_staf():
    """Dashboard staf — menampilkan ringkasan absensi harian dan jam sekolah."""
    today = datetime.now().date()

    pengaturan = Pengaturan.query.first()
    jam_masuk = pengaturan.jam_masuk if pengaturan and pengaturan.jam_masuk else "--:--"
    jam_pulang = pengaturan.jam_pulang if pengaturan and pengaturan.jam_pulang else "--:--"

    hadir = Absensi.query.filter_by(tanggal=today, status='Hadir').count()
    terlambat = Absensi.query.filter_by(tanggal=today, status='Terlambat').count()
    izin = Absensi.query.filter_by(tanggal=today, status='Izin').count()
    sakit = Absensi.query.filter_by(tanggal=today, status='Sakit').count()
    alpa = Absensi.query.filter_by(tanggal=today, status='Alpa').count()
    bolos = Absensi.query.filter_by(tanggal=today, status='Bolos').count()

    semua_kelas = [k[0] for k in db.session.query(Siswa.kelas).distinct().order_by(Siswa.kelas.asc())]

    return render_template(
        'staf/dashboard_staf.html',
        nama=session.get('nama'),
        jam_masuk=jam_masuk,
        jam_pulang=jam_pulang,
        hadir=hadir,
        terlambat=terlambat,
        izin=izin,
        sakit=sakit,
        alpa=alpa,
        bolos=bolos,
        semua_kelas=semua_kelas
    )

# ==================== ENDPOINT UPDATE REALTIME ====================
@staf_bp.route('/get_jam')
@login_required_staf
def get_jam():
    """API kecil untuk memperbarui jam sekolah secara realtime di dashboard."""
    pengaturan = Pengaturan.query.first()
    jam_masuk = pengaturan.jam_masuk if pengaturan and pengaturan.jam_masuk else "--:--"
    jam_pulang = pengaturan.jam_pulang if pengaturan and pengaturan.jam_pulang else "--:--"
    return jsonify({'jam_masuk': jam_masuk, 'jam_pulang': jam_pulang})

# ==================== HALAMAN SCAN QR ====================
@staf_bp.route('/scan')
@login_required_staf
def scan_qr():
    """Halaman scan QR absen."""
    catat_aktivitas(session.get('nama'), "Akses halaman scan QR")
    return render_template('staf/scan_qr.html', nama=session.get('nama'))
