from flask import Blueprint, request
from datetime import datetime
from utils.laporan_pdf import generate_laporan_pdf
from utils.laporan_excel import generate_laporan_excel
from models import Absen

bp = Blueprint("staf_laporan_export", __name__, url_prefix="/staf_laporan_export")

@bp.route("/download")
def download_laporan():
    format = request.args.get("format", "pdf")
    mulai = request.args.get("mulai")
    selesai = request.args.get("selesai")

    periode_mulai = datetime.strptime(mulai, "%Y-%m-%d") if mulai else None
    periode_selesai = datetime.strptime(selesai, "%Y-%m-%d") if selesai else None

    data = Absen.query.all()  # nanti bisa difilter
    data_absen = [{
        "nama": d.nama,
        "jam_masuk": d.jam_masuk,
        "jam_pulang": d.jam_pulang,
        "status": d.status
    } for d in data]

    if format == "excel":
        return generate_laporan_excel(data_absen, "Rini Kartika", "198907182023012001",
            "Laporan Rekapitulasi Absensi Staf", periode_mulai, periode_selesai)
    else:
        return generate_laporan_pdf(data_absen, "Rini Kartika", "198907182023012001",
            "Laporan Rekapitulasi Absensi Staf", periode_mulai, periode_selesai)
