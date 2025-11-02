from flask import Blueprint, render_template

staf_laporan_main = Blueprint('staf_laporan_main', __name__, url_prefix='/staf_laporan')

@staf_laporan_main.route('/')
def laporan_index():
    """
    Halaman utama menu Laporan Staf.
    Menampilkan pilihan laporan (harian, per siswa, per kelas, semua kelas).
    """
    return render_template('staf/laporan_staf.html')
