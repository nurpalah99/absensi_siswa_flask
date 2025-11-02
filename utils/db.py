# utils/db.py
import sqlite3
from flask import g

DATABASE = 'database/absensi.db'

def get_db():
    """Membuka koneksi database SQLite dan menyimpannya di flask.g"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Menutup koneksi database"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_app(app):
    """Mendaftarkan fungsi close_db ke aplikasi Flask"""
    app.teardown_appcontext(close_db)
