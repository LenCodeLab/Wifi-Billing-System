from models import db, Voucher
from app import app
import random, string

def create_voucher(n=10):
    with app.app_context():
        for _ in range(n):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            db.session.add(Voucher(code=code))
        db.session.commit()
        print("Vouchers created!")

if __name__ == "__main__":
    create_voucher()
