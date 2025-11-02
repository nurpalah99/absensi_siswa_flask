# blueprints/staf/staf_pengaturan.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from utils.db import get_db
from utils.decorators import login_required_staf

staf_pengaturan = Blueprint('staf_pengaturan', __name__, url_prefix='/staf/pengaturan')

@staf_pengaturan.route('/')
@login_required_staf
def index():
    db = get_db()
    cursor = db.cursor()

    # Ambil pengaturan (karena tabelnya bernama 'pengaturan')
    cursor.execute("SELECT * FROM pengaturan LIMIT 1")
    pengaturan = cursor.fetchone()

    # Kepala sekolah disimpan di tabel 'users' dengan role = 'kepsek'
    cursor.execute("SELECT nama, nip FROM users WHERE role='kepsek' LIMIT 1")
    kepala = cursor.fetchone()

    # Data operator login
    operator = {
        "nama": session.get('nama'),
        "nip": session.get('nip'),
        "jabatan": session.get('jabatan')
    }

    return render_template(
        'staf/pengaturan_staf.html',
        pengaturan=pengaturan,
        kepala=kepala,
        operator=operator
    )


# ------------------- Simpan pengaturan -------------------
@staf_pengaturan.route('/simpan', methods=['POST'])
@login_required_staf
def simpan_pengaturan():
    db = get_db()
    cursor = db.cursor()

    jam_masuk = request.form.get('jam_masuk')
    jam_pulang = request.form.get('jam_pulang')
    tutup_absen = request.form.get('tutup_absen')  # opsional
    nama_kepsek = request.form.get('nama_kepsek')
    nip_kepsek = request.form.get('nip_kepsek')

    # Update atau tambah jam masuk/pulang
    cursor.execute("SELECT COUNT(*) as jml FROM pengaturan")
    if cursor.fetchone()['jml'] == 0:
        cursor.execute("""
            INSERT INTO pengaturan (jam_masuk, jam_pulang)
            VALUES (?, ?)
        """, (jam_masuk, jam_pulang))
    else:
        cursor.execute("""
            UPDATE pengaturan SET jam_masuk=?, jam_pulang=?
        """, (jam_masuk, jam_pulang))

    # Update kepala sekolah di tabel users
    cursor.execute("SELECT id FROM users WHERE role='kepsek'")
    kepsek = cursor.fetchone()
    if kepsek:
        cursor.execute("""
            UPDATE users SET nama=?, nip=? WHERE id=?
        """, (nama_kepsek, nip_kepsek, kepsek['id']))
    else:
        cursor.execute("""
            INSERT INTO users (nama, username, password, nip, role, status)
            VALUES (?, ?, 'default', ?, 'kepsek', 'aktif')
        """, (nama_kepsek, nama_kepsek.lower().replace(' ', ''), nip_kepsek))

    db.commit()
    flash("✅ Pengaturan berhasil disimpan.", "success")
    return redirect(url_for('staf_pengaturan.index'))


# ------------------- Pulang Massal -------------------
@staf_pengaturan.route('/pulang_massal', methods=['POST'])
@login_required_staf
def pulang_massal():
    db = get_db()
    cursor = db.cursor()

    alasan = request.form.get('alasan')
    waktu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute("""
        UPDATE absensi 
        SET waktu=?, status='Pulang', keterangan=?
        WHERE tanggal=date('now') AND status!='Pulang'
    """, (waktu, f"Pulang massal: {alasan}"))

    db.commit()
    flash("🚪 Pulang massal berhasil diproses.", "info")
    return redirect(url_for('staf_pengaturan.index'))
