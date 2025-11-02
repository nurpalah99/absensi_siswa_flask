from flask import Blueprint, render_template, request, send_file, session, flash, redirect, url_for
from datetime import datetime
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from sqlalchemy import func, distinct
from ext import db
from models.absensi import Absensi
from models.siswa import Siswa
from .staf_utils import require_staf, catat_aktivitas

staf_laporan_kelas = Blueprint('staf_laporan_kelas', __name__, url_prefix='/staf/laporan_kelas')


@staf_laporan_kelas.route('/laporan_per_kelas', methods=['GET', 'POST'])
@require_staf
def laporan_per_kelas():
    semua_kelas = [k[0] for k in db.session.query(Siswa.kelas).distinct().order_by(Siswa.kelas.asc())]
    kelas_filter = request.form.get('kelas', '') or request.args.get('kelas', '')
    tgl_awal = request.form.get('tgl_awal') or request.args.get('tgl_awal') or datetime.now().replace(day=1).strftime('%Y-%m-%d')
    tgl_akhir = request.form.get('tgl_akhir') or request.args.get('tgl_akhir') or datetime.now().strftime('%Y-%m-%d')
    data_rekap = []
    if kelas_filter:
        siswa_list = Siswa.query.filter_by(kelas=kelas_filter, status='Aktif').order_by(Siswa.nama.asc()).all()
        for s in siswa_list:
            hadir = Absensi.query.filter_by(nis=s.nis, status='Hadir').filter(Absensi.tanggal.between(tgl_awal, tgl_akhir)).count()
            terlambat = Absensi.query.filter_by(nis=s.nis, status='Terlambat').filter(Absensi.tanggal.between(tgl_awal, tgl_akhir)).count()
            sakit = Absensi.query.filter_by(nis=s.nis, status='Sakit').filter(Absensi.tanggal.between(tgl_awal, tgl_akhir)).count()
            izin = Absensi.query.filter_by(nis=s.nis, status='Izin').filter(Absensi.tanggal.between(tgl_awal, tgl_akhir)).count()
            alpa = Absensi.query.filter_by(nis=s.nis, status='Alpa').filter(Absensi.tanggal.between(tgl_awal, tgl_akhir)).count()
            bolos = Absensi.query.filter_by(nis=s.nis, status='Bolos').filter(Absensi.tanggal.between(tgl_awal, tgl_akhir)).count()
            total = hadir + terlambat + sakit + izin + alpa + bolos
            data_rekap.append({'nis': s.nis, 'nama': s.nama, 'kelas': s.kelas,
                               'hadir': hadir, 'terlambat': terlambat, 'sakit': sakit,
                               'izin': izin, 'alpa': alpa, 'bolos': bolos, 'total': total})
        catat_aktivitas(session.get('nama'), f"Lihat laporan per kelas {kelas_filter} ({tgl_awal} - {tgl_akhir})")
    return render_template('staf/laporan_per_kelas.html', semua_kelas=semua_kelas, kelas_filter=kelas_filter,
                           tgl_awal=tgl_awal, tgl_akhir=tgl_akhir, data_rekap=data_rekap)
