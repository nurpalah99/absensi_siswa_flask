from flask import Blueprint, render_template, request, send_file, session
from datetime import datetime
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from sqlalchemy import func, distinct
from ext import db
from models.absensi import Absensi
from models.siswa import Siswa
from .staf_utils import require_staf, catat_aktivitas

staf_laporan_semua = Blueprint('staf_laporan_semua', __name__, url_prefix='/staf/laporan_semua')


@staf_laporan_semua.route('/laporan_semua', methods=['GET', 'POST'])
@require_staf
def laporan_semua():
    tgl_awal = request.form.get('tgl_awal') or datetime.now().replace(day=1).strftime('%Y-%m-%d')
    tgl_akhir = request.form.get('tgl_akhir') or datetime.now().strftime('%Y-%m-%d')
    kelas_list = [k[0] for k in db.session.query(Siswa.kelas).distinct().order_by(Siswa.kelas.asc())]
    data_rekap = []
    total = {'hadir': 0, 'terlambat': 0, 'sakit': 0, 'izin': 0, 'alpa': 0, 'bolos': 0}
    for kelas in kelas_list:
        def hitung(status):
            return db.session.query(func.count(distinct(Absensi.nis))).join(Siswa, Siswa.nis == Absensi.nis).filter(
                Siswa.kelas == kelas, Absensi.status == status,
                Absensi.tanggal.between(tgl_awal, tgl_akhir)).scalar()
        hadir = hitung('Hadir'); terlambat = hitung('Terlambat'); sakit = hitung('Sakit')
        izin = hitung('Izin'); alpa = hitung('Alpa'); bolos = hitung('Bolos')
        data_rekap.append({'kelas': kelas, 'hadir': hadir, 'terlambat': terlambat,
                           'sakit': sakit, 'izin': izin, 'alpa': alpa, 'bolos': bolos})
        for k in total: total[k] += locals()[k]
    catat_aktivitas(session.get('nama'), f"Lihat laporan semua kelas ({tgl_awal}-{tgl_akhir})")
    return render_template('staf/laporan_semua.html', data_rekap=data_rekap, total_semua=total,
                           tgl_awal=tgl_awal, tgl_akhir=tgl_akhir)
