from flask import Flask, redirect, url_for, session
from flask_cors import CORS
from flask_session import Session
from datetime import timedelta, datetime
from config import config_map
from ext import db, bcrypt
from blueprints import register_blueprints
from utils.logger import log_info, log_error
from models import load_models


# =====================================================
# 🔁 HELPER GLOBAL: Redirect sesuai role
# =====================================================
def redirect_by_role(role: str):
    """Mengembalikan URL endpoint sesuai peran pengguna."""
    mapping = {
        'admin': 'admin.dashboard_admin',
        'staf': 'staf.dashboard_staf',
        'bk': 'staf.dashboard_staf',
        'waka': 'staf.dashboard_staf',
        'walikelas': 'walikelas.dashboard_wali',
        'operator': 'operator.dashboard_operator',
    }
    return mapping.get(role, 'auth.login')


# =====================================================
# 🧩 FUNGSI UTAMA PEMBUAT APP
# =====================================================
def create_app():
    import os
    env = os.getenv("FLASK_ENV", "dev")

    app = Flask(__name__)
    app.config.from_object(config_map[env])
    app.permanent_session_lifetime = timedelta(minutes=30)

    # Inisialisasi ekstensi
    CORS(app)
    Session(app)

    if not hasattr(app, 'extensions') or 'sqlalchemy' not in app.extensions:
        db.init_app(app)

    # ===============================
    # 🔹 PASTIKAN SEMUA MODEL DIKENALI
    # ===============================
    from models import load_models
    from models.user_activity import UserActivity  # 🚀 Import langsung agar terdaftar

    with app.app_context():
        load_models()
        db.create_all()

    # Registrasi blueprint
    from blueprints import register_blueprints
    register_blueprints(app)


    @app.route('/')
    def index():
        role = session.get('role')
        if not role:
            return redirect(url_for('auth.login'))
        return redirect(url_for(redirect_by_role(role)))

    @app.context_processor
    def inject_globals():
        return dict(datetime=datetime)

    print(f"\n✅ Flask environment: {env.upper()}")
    print("✅ Semua blueprint berhasil diregistrasi.\n")

    # Tampilkan daftar blueprint aktif
    print("=== Blueprint Aktif Sekarang ===")
    for name, bp in app.blueprints.items():
        print(f" - {name:20s} | prefix: {bp.url_prefix}")
    print("=================================\n")

    return app


# =====================================================
# 🚀 MAIN EXECUTION (LOCAL MODE)
# =====================================================
if __name__ == '__main__':
    app = create_app()
    print("\n🌐 Menjalankan server lokal (HTTP, mode sekolah offline)...")
    print("Pastikan HP & laptop terhubung ke Wi-Fi yang sama.")
    print("👉 Akses di laptop: http://127.0.0.1:5000")
    print("👉 Akses di HP guru/staf: http://<IP_laptop>:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
