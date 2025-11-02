
# models/absensi.py
from ext import db
from datetime import datetime

class Absensi(db.Model):
    __tablename__ = "absensi"

    id = db.Column(db.Integer, primary_key=True)
    nis = db.Column(db.String(20), nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    kelas = db.Column(db.String(50), nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    jam_masuk = db.Column(db.Time)
    jam_pulang = db.Column(db.Time)
    status = db.Column(db.String(20), default="Hadir")
    keterangan = db.Column(db.String(255))
    is_locked = db.Column(db.Integer, default=0)
    scanner_id = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("nis", "tanggal", name="unique_absen_per_hari"),
    )

    def __repr__(self):
        return f"<Absensi {self.nis} {self.tanggal} {self.status}>"
