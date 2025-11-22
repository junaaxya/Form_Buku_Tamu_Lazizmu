from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class GuestFollow(db.Model):
    __tablename__ = "guests_follow"
    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(30))
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(255))
    institution = db.Column(db.String(120))
    purpose = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30))
    photo_filename = db.Column(db.String(255))
    follow_proof = db.Column(db.String(255))   # 🟢 file bukti follow
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_row(self):
        ts = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return [
            self.id, self.name, self.purpose, self.phone or "",
            self.photo_filename or "", self.follow_proof or "", ts
        ]
