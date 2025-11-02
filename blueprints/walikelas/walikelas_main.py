from flask import render_template, session
from utils.role_required import role_required
from . import walikelas_bp

@walikelas_bp.route("/dashboard")
@role_required(["walikelas", "admin"])
def dashboard_wali():
    nama_user = session.get("nama", "Wali Kelas")
    return render_template("walikelas/dashboard_walikelas.html", nama_user=nama_user)
