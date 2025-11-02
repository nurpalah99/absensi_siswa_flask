# routes/staf_laporan_harian.py
from flask import Blueprint, render_template, request
from datetime import datetime
from models.absensi import Absensi
from ext import db

bp = Blueprint("staf_laporan_harian", __name__, url_prefix="/staf_laporan")

@bp.route("/harian", methods=["GET", "POST"])
def laporan_harian():
    today = datetime.today().date()
    tanggal_mulai = tanggal_selesai = today

    if request.method == "POST":
        try:
            tanggal_mulai = datetime.strptime(request.form.get("tanggal_mulai", str(today)), "%Y-%m-%d").date()
            tanggal_selesai = datetime.strptime(request.form.get("tanggal_selesai", str(today)), "%Y-%m-%d").date()
        except Exception as e:
            print(f"[ERROR] Format tanggal tidak valid: {e}")
            tanggal_mulai = tanggal_selesai = today

    # ✅ Query langsung cocok dengan tipe kolom (Date)
    data = Absensi.query.filter(
        Absensi.tanggal.between(tanggal_mulai, tanggal_selesai)
    ).all()

    print(f"[DEBUG] Filter tanggal {tanggal_mulai} s.d {tanggal_selesai} → {len(data)} data ditemukan")

    # 🔁 Rekap kehadiran
    rekap = {}
    for d in data:
        rekap[d.status] = rekap.get(d.status, 0) + 1
    total_siswa = len(data)

    return render_template(
        "staf/laporan_harian.html",
        tanggal_mulai=tanggal_mulai.strftime("%Y-%m-%d"),
        tanggal_selesai=tanggal_selesai.strftime("%Y-%m-%d"),
        rekap=rekap,
        total_siswa=total_siswa,
        kepala_nama="Kumasrin, SP.",
        kepala_nip="196806272007011010",
        operator_nama="Rini Kartika",
        operator_nip="198907182023012001",
    )
