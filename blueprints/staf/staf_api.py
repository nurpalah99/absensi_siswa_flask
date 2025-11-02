from flask import Blueprint, jsonify
from datetime import datetime
from ext import db
from models import Absensi, Siswa, Pengaturan

staf_api = Blueprint("staf_api", __name__, url_prefix="/staf/api")


@staf_api.route("/status-summary")
def status_summary():
    """🔹 Ringkasan status absensi hari ini untuk dashboard staf."""
    today = datetime.now().date()

    # Ambil semua data absensi hari ini
    absensi_hari_ini = Absensi.query.filter_by(tanggal=today).all()

    # Hitung berdasarkan status
    summary = {
        "Hadir": 0,
        "Terlambat": 0,
        "Izin": 0,
        "Sakit": 0,
        "Alpa": 0,
        "Pulang": 0
    }

    for absen in absensi_hari_ini:
        if absen.status in summary:
            summary[absen.status] += 1

    # Ambil pengaturan jam kerja
    pengaturan = Pengaturan.query.first()
    jam_masuk = pengaturan.jam_masuk if pengaturan and pengaturan.jam_masuk else "--:--"
    jam_pulang = pengaturan.jam_pulang if pengaturan and pengaturan.jam_pulang else "--:--"

    # Format response JSON sesuai dashboard
    return jsonify({
        "jam_masuk": jam_masuk,
        "jam_pulang": jam_pulang,
        **summary
    })


@staf_api.route('/recent-absen')
def recent_absen():
    """🔹 Menampilkan 10 data absensi terbaru (urut paling baru di atas)."""
    data = Absensi.query.order_by(Absensi.id.desc()).limit(10).all()

    hasil = []
    for a in data:
        hasil.append({
            "nama": getattr(a, "nama", "-"),
            "kelas": getattr(a, "kelas", "-"),
            "status": getattr(a, "status", "-"),
            "waktu": (
                a.jam_pulang.strftime("%H:%M:%S")
                if a.status == "Pulang" and a.jam_pulang
                else a.jam_masuk.strftime("%H:%M:%S") if a.jam_masuk else "-"
            )
        })

    return jsonify(hasil)
