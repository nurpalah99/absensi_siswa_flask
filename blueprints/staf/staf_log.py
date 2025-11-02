from flask import Blueprint, render_template, send_file, session, request
from datetime import datetime
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from models.user_activity import UserActivity
from .staf_utils import require_staf, catat_aktivitas

staf_log = Blueprint('staf_log', __name__, url_prefix='/staf/log')


@staf_log.route('/log_aktivitas', methods=['GET', 'POST'])
@require_staf
def log_aktivitas():
    tgl_awal = request.form.get('tgl_awal') or datetime.now().replace(day=1).strftime('%Y-%m-%d')
    tgl_akhir = request.form.get('tgl_akhir') or datetime.now().strftime('%Y-%m-%d')
    aktivitas_list = UserActivity.query.filter(UserActivity.timestamp.between(tgl_awal, tgl_akhir)).order_by(UserActivity.timestamp.desc()).all()
    return render_template('staf/log_aktivitas.html', aktivitas_list=aktivitas_list, tgl_awal=tgl_awal, tgl_akhir=tgl_akhir)
