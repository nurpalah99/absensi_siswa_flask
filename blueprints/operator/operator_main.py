from flask import render_template, session
from utils.role_required import role_required
from . import operator_bp

@operator_bp.route("/dashboard")
@role_required(["operator", "admin"])
def dashboard_operator():
    nama_user = session.get("nama", "Operator")
    return render_template("operator/dashboard_operator.html", nama_user=nama_user)
