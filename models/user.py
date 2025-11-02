from datetime import datetime
from ext import db, bcrypt


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    nip = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(30), nullable=False, default="staf")
    wali_kelas = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="aktif")
    foto = db.Column(db.String(200), nullable=True)
    last_login = db.Column(db.DateTime, default=datetime.now)

    # ======================================================
    # 🔒 PASSWORD HANDLING
    # ======================================================
    def set_password(self, plain_password: str):
        """Set password baru dengan hash bcrypt."""
        self.password = bcrypt.generate_password_hash(plain_password).decode("utf-8")

    def check_password(self, plain_password: str) -> bool:
        """Verifikasi password, dengan fallback plaintext dan auto-upgrade."""
        try:
            if bcrypt.check_password_hash(self.password, plain_password):
                return True
        except ValueError:
            # fallback plaintext lama (auto-upgrade)
            if self.password == plain_password:
                self.set_password(plain_password)
                db.session.commit()
                print(f"🔁 Password user '{self.username}' diupgrade ke bcrypt.")
                return True
        return False

    # ======================================================
    # 🧩 HELPER METHOD TAMBAHAN
    # ======================================================
    @classmethod
    def get_by_username(cls, username: str):
        """Ambil user berdasarkan username."""
        return cls.query.filter_by(username=username).first()

    def update_last_login(self):
        """Perbarui waktu login terakhir."""
        self.last_login = datetime.now()
        db.session.commit()

    def is_active(self) -> bool:
        """Cek apakah user aktif."""
        return self.status.lower() == "aktif"

    def is_role(self, roles: list) -> bool:
        """Cek apakah user memiliki salah satu role tertentu."""
        return self.role in roles

    def __repr__(self):
        return f"<User {self.nama} ({self.role})>"
