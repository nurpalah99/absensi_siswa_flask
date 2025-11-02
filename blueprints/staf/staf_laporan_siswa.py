from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session
from io import BytesIO
from datetime import datetime
from ext import db
import pandas as pd
from fpdf import FPDF
from models.absensi import Absensi
from models.siswa import Siswa
from .staf_utils import require_staf, catat_aktivitas

staf_laporan_siswa = Blueprint('staf_laporan_siswa', __name__, url_prefix='/staf/laporan_siswa')


@staf_laporan_siswa.route('/laporan_per_siswa', methods=['GET', 'POST'])
@require_staf
def laporan_per_siswa():
    semua_siswa = Siswa.query.order_by(Siswa.kelas.asc(), Siswa.nama.asc()).all()
    data = []
    nis_filter = request.form.get('nis', '') or request.args.get('nis', '')
    tgl_awal = request.form.get('tgl_awal') or request.args.get('tgl_awal') or datetime.now().replace(day=1).strftime('%Y-%m-%d')
    tgl_akhir = request.form.get('tgl_akhir') or request.args.get('tgl_akhir') or datetime.now().strftime('%Y-%m-%d')
    if nis_filter:
        data = Absensi.query.filter(
            Absensi.nis == nis_filter,
            Absensi.tanggal.between(tgl_awal, tgl_akhir)
        ).order_by(Absensi.tanggal.asc()).all()
        catat_aktivitas(session.get('nama'), f"Lihat laporan per siswa {nis_filter} ({tgl_awal} - {tgl_akhir})")
    return render_template('staf/laporan_per_siswa.html',
                           semua_siswa=semua_siswa,
                           data=data,
                           nis_filter=nis_filter,
                           tgl_awal=tgl_awal,
                           tgl_akhir=tgl_akhir)

@staf_laporan_siswa.route('/laporan_per_siswa/excel')
@require_staf
def export_laporan_per_siswa_excel():
    nis = request.args.get('nis')
    tgl_awal = request.args.get('tgl_awal')
    tgl_akhir = request.args.get('tgl_akhir')
    if not nis:
        flash('Pilih siswa terlebih dahulu.', 'warning')
        return redirect(url_for('staf_laporan_siswa.laporan_per_siswa'))
    siswa = Siswa.query.filter_by(nis=nis).first()
    data_absen = Absensi.query.filter(Absensi.nis == nis, Absensi.tanggal.between(tgl_awal, tgl_akhir)).order_by(Absensi.tanggal.asc()).all()
    rows = []
    for idx, a in enumerate(data_absen, start=1):
        rows.append({
            "No": idx, "Tanggal": a.tanggal, "Status": a.status,
            "Jenis Absen": a.jenis_absen or '-', "Waktu": a.waktu.strftime("%H:%M") if a.waktu else "-",
            "Keterangan": a.keterangan or "-"
        })
    df = pd.DataFrame(rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Laporan Siswa')
    output.seek(0)
    catat_aktivitas(session.get('nama'), f"Ekspor Excel laporan siswa {nis} ({tgl_awal} - {tgl_akhir})")
    return send_file(output, as_attachment=True, download_name=f"laporan_{siswa.nama}_{tgl_awal}_sd_{tgl_akhir}.xlsx")

@staf_laporan_siswa.route('/laporan_per_siswa/pdf')
@require_staf
def export_laporan_per_siswa_pdf():
    nis = request.args.get('nis')
    tgl_awal = request.args.get('tgl_awal')
    tgl_akhir = request.args.get('tgl_akhir')
    siswa = Siswa.query.filter_by(nis=nis).first()
    data_absen = Absensi.query.filter(Absensi.nis == nis, Absensi.tanggal.between(tgl_awal, tgl_akhir)).order_by(Absensi.tanggal.asc()).all()
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "LAPORAN ABSENSI SISWA", ln=True, align="C")
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Nama: {siswa.nama}", ln=True)
    pdf.cell(0, 8, f"Kelas: {siswa.kelas}", ln=True)
    pdf.cell(0, 8, f"NIS: {siswa.nis}", ln=True)
    pdf.cell(0, 8, f"Periode: {tgl_awal} s.d {tgl_akhir}", ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(12, 8, "No", 1)
    pdf.cell(30, 8, "Tanggal", 1)
    pdf.cell(30, 8, "Status", 1)
    pdf.cell(35, 8, "Jenis Absen", 1)
    pdf.cell(25, 8, "Waktu", 1)
    pdf.cell(58, 8, "Keterangan", 1, 1)
    pdf.set_font("Arial", '', 9)
    for idx, a in enumerate(data_absen, start=1):
        pdf.cell(12, 8, str(idx), 1)
        pdf.cell(30, 8, str(a.tanggal), 1)
        pdf.cell(30, 8, a.status or '-', 1)
        pdf.cell(35, 8, a.jenis_absen or '-', 1)
        pdf.cell(25, 8, a.waktu.strftime("%H:%M") if a.waktu else '-', 1)
        pdf.cell(58, 8, a.keterangan or '-', 1, 1)
    output = BytesIO(pdf.output(dest='S').encode('latin1'))
    catat_aktivitas(session.get('nama'), f"Ekspor PDF laporan siswa {nis} ({tgl_awal} - {tgl_akhir})")
    return send_file(output, as_attachment=True, download_name=f"laporan_absensi_{siswa.nama}_{tgl_awal}_sd_{tgl_akhir}.pdf")
