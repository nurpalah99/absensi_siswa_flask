from flask import Blueprint
from .staf_main import staf_bp
from .staf_siswa import staf_siswa
from .staf_absen import staf_absen
from .staf_laporan_kelas import staf_laporan_kelas
from .staf_laporan_siswa import staf_laporan_siswa
from .staf_laporan_semua import staf_laporan_semua
from .staf_pengaturan import staf_pengaturan
from .staf_log import staf_log
from .staf_api import staf_api

def register_staf_blueprints(app):
    app.register_blueprint(staf_bp)
    app.register_blueprint(staf_siswa)
    app.register_blueprint(staf_absen)
    app.register_blueprint(staf_laporan_kelas)
    app.register_blueprint(staf_laporan_siswa)
    app.register_blueprint(staf_laporan_semua)
    app.register_blueprint(staf_pengaturan)
    app.register_blueprint(staf_log)
    app.register_blueprint(staf_api)
