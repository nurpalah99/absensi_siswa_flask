from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from ext import db
from models.siswa import Siswa
from utils.decorators import login_required_staf
from .staf_utils import catat_aktivitas
from sqlalchemy import func
import io
import pandas as pd
from flask import send_file

staf_siswa = Blueprint('staf_siswa', __name__, url_prefix='/staf/siswa')

# ===========================================================
# 🧩 DAFTAR SISWA
# ===========================================================
@staf_siswa.route('/')
@login_required_staf
def daftar_siswa():
    kelas_filter = (request.args.get('kelas') or "").strip().replace('\xa0', ' ')
    cari_nama = (request.args.get('cari') or "").strip()
    status_filter = (request.args.get('status') or "").strip()

    print("🧩 [DEBUG] Filter diterima →", f"kelas='{kelas_filter}'", f"status='{status_filter}'", f"cari='{cari_nama}'")

    query = Siswa.query

    if cari_nama:
        query = query.filter(Siswa.nama.ilike(f"%{cari_nama}%"))

    if kelas_filter:
        kelas_filter_norm = kelas_filter.upper().replace('\xa0', ' ')
        query = query.filter(func.replace(func.upper(func.trim(Siswa.kelas)), '\xa0', ' ').ilike(f"%{kelas_filter_norm}%"))

    if status_filter and status_filter.lower() not in ["semua", "semua status", ""]:
        query = query.filter(func.lower(func.trim(Siswa.status)) == status_filter.lower())

    semua_siswa = query.order_by(Siswa.kelas.asc(), Siswa.nama.asc()).all()

    semua_kelas = sorted(list({
        (" ".join((k or "").split())).strip()
        for k in [x[0] for x in db.session.query(Siswa.kelas).distinct().all()]
        if k
    }))

    print(f"✅ [DEBUG] Total hasil siswa: {len(semua_siswa)}")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("staf/_tabel_siswa.html", semua_siswa=semua_siswa)

    return render_template(
        "staf/data_siswa.html",
        semua_siswa=semua_siswa,
        semua_kelas=semua_kelas,
        kelas_filter=kelas_filter,
        status_filter=status_filter,
        cari_nama=cari_nama,
    )

# ===========================================================
# 🧩 TAMBAH SISWA
# ===========================================================
@staf_siswa.route('/tambah', methods=['GET', 'POST'])
@login_required_staf
def tambah_siswa():
    semua_kelas = [k[0] for k in db.session.query(Siswa.kelas).distinct().order_by(Siswa.kelas.asc())]

    if request.method == 'POST':
        nis = request.form['nis'].strip()
        nama = request.form['nama'].strip()
        kelas = request.form['kelas'].strip()
        status = request.form.get('status', 'Aktif').capitalize()

        if not nis or not nama or not kelas:
            flash("⚠️ Semua field wajib diisi.", "warning")
            return redirect(url_for('staf_siswa.tambah_siswa'))

        if Siswa.query.filter_by(nis=nis).first():
            flash(f"❌ NIS {nis} sudah terdaftar, tidak bisa menambah data duplikat.", "danger")
            return redirect(url_for('staf_siswa.tambah_siswa'))

        siswa_baru = Siswa(nis=nis, nama=nama, kelas=kelas, status=status)
        db.session.add(siswa_baru)
        db.session.commit()

        catat_aktivitas(session.get('nama'), f"Tambah siswa baru: {nama} ({kelas})")
        flash("✅ Data siswa berhasil ditambahkan.", "success")
        return redirect(url_for('staf_siswa.daftar_siswa'))

    return render_template('staf/tambah_siswa.html', semua_kelas=semua_kelas)

# ===========================================================
# 🧩 CEK NIS — AJAX
# ===========================================================
@staf_siswa.route('/cek_nis', methods=['GET'])
@login_required_staf
def cek_nis():
    nis = (request.args.get('nis') or "").strip()
    if not nis:
        return jsonify({'status': 'error', 'message': 'NIS belum diisi.'})

    siswa = Siswa.query.filter_by(nis=nis).first()
    if siswa:
        return jsonify({
            'status': 'exists',
            'message': f"NIS {nis} sudah terdaftar.",
            'nama': siswa.nama,
            'kelas': siswa.kelas
        })
    return jsonify({'status': 'available', 'message': 'NIS tersedia untuk digunakan.'})

# ===========================================================
# 🧩 EDIT SISWA
# ===========================================================
@staf_siswa.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required_staf
def edit_siswa(id):
    siswa = Siswa.query.get_or_404(id)
    semua_kelas = [k[0] for k in db.session.query(Siswa.kelas).distinct().order_by(Siswa.kelas.asc())]

    if request.method == 'POST':
        siswa.nama = request.form['nama']
        siswa.kelas = request.form['kelas']
        siswa.status = request.form['status']
        db.session.commit()

        catat_aktivitas(session.get('nama'), f"Edit siswa: {siswa.nama} ({siswa.kelas})")
        flash("✅ Data siswa berhasil diperbarui.", "success")
        return redirect(url_for('staf_siswa.daftar_siswa'))

    return render_template('staf/edit_siswa.html', siswa=siswa, semua_kelas=semua_kelas)

# ===========================================================
# 🧩 HAPUS SISWA
# ===========================================================
@staf_siswa.route('/hapus/<int:id>', methods=['POST'])
@login_required_staf
def hapus_siswa(id):
    siswa = Siswa.query.get_or_404(id)
    nama, kelas = siswa.nama, siswa.kelas
    db.session.delete(siswa)
    db.session.commit()

    catat_aktivitas(session.get('nama'), f"Hapus siswa: {nama} ({kelas})")
    flash("🗑️ Data siswa berhasil dihapus.", "info")
    return redirect(url_for('staf_siswa.daftar_siswa'))



# ===========================================================
# 🧩 EKSPOR DATA SISWA KE EXCEL
# ===========================================================
@staf_siswa.route('/ekspor_excel')
@login_required_staf
def ekspor_siswa_excel():
    siswa_list = Siswa.query.order_by(Siswa.kelas.asc(), Siswa.nama.asc()).all()
    if not siswa_list:
        flash("⚠️ Tidak ada data siswa untuk diekspor.", "warning")
        return redirect(url_for('staf_siswa.daftar_siswa'))

    data = [{
        "NIS": s.nis,
        "Nama": s.nama,
        "Kelas": s.kelas,
        "Status": s.status
    } for s in siswa_list]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Data Siswa")

    output.seek(0)
    catat_aktivitas(session.get("nama"), f"Ekspor data siswa ke Excel ({len(siswa_list)} baris)")
    return send_file(
        output,
        as_attachment=True,
        download_name="data_siswa.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ===========================================================
# 🧩 IMPOR DATA SISWA DARI FILE EXCEL
# ===========================================================
@staf_siswa.route('/impor_siswa_excel', methods=['POST'])
@login_required_staf
def impor_siswa_excel():
    file = request.files.get('file')
    if not file:
        flash("❌ Tidak ada file yang diunggah.", "danger")
        return redirect(url_for('staf_siswa.daftar_siswa'))

    try:
        df = pd.read_excel(file)
        total_tambah = total_update = 0

        for _, row in df.iterrows():
            nis = str(row.get("NIS")).strip()
            nama = str(row.get("Nama")).strip()
            kelas = str(row.get("Kelas")).strip()
            status = str(row.get("Status", "Aktif")).strip().capitalize()

            if not nis or not nama or not kelas:
                continue

            siswa = Siswa.query.filter_by(nis=nis).first()
            if siswa:
                siswa.nama = nama
                siswa.kelas = kelas
                siswa.status = status
                total_update += 1
            else:
                db.session.add(Siswa(nis=nis, nama=nama, kelas=kelas, status=status))
                total_tambah += 1

        db.session.commit()
        catat_aktivitas(session.get("nama"), f"Impor Excel siswa: tambah {total_tambah}, update {total_update}")
        flash(f"✅ Impor selesai — {total_tambah} data baru, {total_update} diperbarui.", "success")

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR impor_siswa_excel] {type(e).__name__}: {e}")
        flash("❌ Gagal memproses file Excel. Pastikan format kolom benar (NIS, Nama, Kelas, Status).", "danger")

    return redirect(url_for('staf_siswa.daftar_siswa'))
