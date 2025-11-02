from flask import Blueprint

walikelas_bp = Blueprint("walikelas", __name__, url_prefix="/walikelas")

from . import walikelas_main  # pastikan file walikelas_main.py ada di folder yang sama
