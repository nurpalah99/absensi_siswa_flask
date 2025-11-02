from ext import db
from datetime import datetime


class UserActivity(db.Model):
    __tablename__ = "user_activity"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    username = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(30), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<UserActivity {self.username} - {self.action} @ {self.timestamp:%Y-%m-%d %H:%M:%S}>"

    # ======================================================
    # 🧩 Fungsi pembuat log otomatis
    # ======================================================
    @classmethod
    def log(cls, username, action, user_id=None, role=None, ip_address=None, user_agent=None):
        """Simpan log aktivitas user ke database."""
        log_entry = cls(
            username=username,
            user_id=user_id,
            role=role,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.session.add(log_entry)
        db.session.commit()
        print(f"🧾 Log: {username} | {action} | {datetime.now():%H:%M:%S}")

    @classmethod
    def recent(cls, limit=20):
        """Ambil daftar log terbaru (default 20)."""
        return cls.query.order_by(cls.timestamp.desc()).limit(limit).all()
