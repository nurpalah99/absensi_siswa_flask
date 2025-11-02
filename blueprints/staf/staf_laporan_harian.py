# blueprints/staf/staf_laporan_harian.py
from flask import Blueprint, render_template, request, session
from datetime import datetime
from models.absensi import Absensi
from sqlalchemy import func
from ext import db  # gunakan koneksi SQLAlchemy yang sama

staf_laporan_harian = Blueprint('staf_laporan_harian', __name__, url_prefix='/staf_laporan')

@staf_laporan_harian.route('/harian', methods=['GET', 'POST'])
def laporan_harian():
    # Ambil tanggal dari form (default: hari ini)
    tanggal_str = request.form.get('tanggal') or datetime.now().strftime('%Y-%m-%d')
    try:
        tanggal_obj = datetime.strptime(tanggal_str, "%Y-%m-%d").date()
    except ValueError:
        tanggal_obj = datetime.now().date()

    # Query absensi berdasarkan tanggal (pakai ORM)
    hasil = (
        db.session.query(Absensi.status, func.count(Absensi.status))
        .filter(func.date(Absensi.tanggal) == tanggal_obj)
        .group_by(Absensi.status)
        .all()
    )

    # Siapkan struktur rekap default
    rekap = {
        "Hadir": 0,
        "Terlambat": 0,
        "Izin": 0,
        "Sakit": 0,
        "Alpa": 0,
        "Bolos": 0
    }

    for status, jumlah in hasil:
        key = (status or "").capitalize()
        if key in rekap:
            rekap[key] = jumlah
        else:
            # Kalau ada status baru (misal “Dispensasi”), tambahkan otomatis
            rekap[key] = jumlah

    total_siswa = sum(rekap.values())

    # Data operator dan kepala sekolah
    operator_nama = session.get('nama', 'Operator Sekolah')
    operator_nip = session.get('nip', '-')
    kepala_nama = "K U M A S R I N, SP."
    kepala_nip = "19680627 200701 1 010"

    # Kirim ke template
    return render_template(
        'staf/laporan_harian.html',
        tanggal=tanggal_str,
        rekap=rekap,
        total_siswa=total_siswa,
        operator_nama=operator_nama,
        operator_nip=operator_nip,
        kepala_nama=kepala_nama,
        kepala_nip=kepala_nip
    )
