from ext import db
from datetime import datetime

class Pengaturan(db.Model):
    __tablename__ = 'pengaturan'
    id = db.Column(db.Integer, primary_key=True)

    # ====== Pengaturan Jam Lama (masih bisa dipakai) ======
    jam_masuk = db.Column(db.String(10), nullable=True)
    jam_pulang = db.Column(db.String(10), nullable=True)

    # ====== Mode Key-Value (dinamis) ======
    kunci = db.Column(db.String(100), unique=True, nullable=True)
    nilai = db.Column(db.String(255), nullable=True)

    # ====== Tambahan untuk deteksi pembaruan absensi ======
    last_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        if self.kunci:
            return f'<Pengaturan {self.kunci}={self.nilai}>'
        return f'<Pengaturan jam_masuk={self.jam_masuk}, jam_pulang={self.jam_pulang}>'
