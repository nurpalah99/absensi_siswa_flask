from ext import db

class Siswa(db.Model):
    __tablename__ = 'siswa'
    id = db.Column(db.Integer, primary_key=True)
    nis = db.Column(db.String(50), unique=True, nullable=False)
    nama = db.Column(db.String(150), nullable=False)
    kelas = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Aktif')
    foto = db.Column(db.String(200), nullable=True)
