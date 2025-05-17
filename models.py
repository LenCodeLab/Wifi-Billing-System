from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Voucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True, nullable=False)
    used = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(15), nullable=True)
    # TODO: Add expiration, data allocation, or user fields as needed
