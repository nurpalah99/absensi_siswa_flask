from ext import db

class WaktuPulang(db.Model):
    __tablename__ = "waktu_pulang"
    id = db.Column(db.Integer, primary_key=True)
    hari = db.Column(db.String(10), unique=True)  # Senin, Selasa, ...
    jam_pulang = db.Column(db.Time)

    def __repr__(self):
        return f"<WaktuPulang {self.hari}: {self.jam_pulang}>"
