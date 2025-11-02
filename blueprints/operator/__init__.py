from flask import Blueprint

operator_bp = Blueprint("operator", __name__, url_prefix="/operator")

from . import operator_main
