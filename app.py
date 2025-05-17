import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from models import db, Voucher
from mpesa_stk import initiate_stk_push

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wifi_billing.db'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

class User(UserMixin):
    def __init__(self, voucher):
        self.id = voucher.code
        self.code = voucher.code
        self.phone = voucher.phone

@login_manager.user_loader
def load_user(code):
    voucher = Voucher.query.filter_by(code=code, used=True).first()
    if voucher:
        return User(voucher)
    return None

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/pay')
def pay_page():
    return render_template('pay.html')

@app.route('/api/login', methods=['POST'])
def login():
    code = request.json.get('voucher')
    voucher = Voucher.query.filter_by(code=code, used=False).first()
    if voucher:
        voucher.used = True
        db.session.commit()
        user = User(voucher)
        login_user(user)
        return jsonify(success=True)
    return jsonify(success=False, message="Invalid or used voucher")

@app.route('/api/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_page'))

@app.route('/api/dashboard')
@login_required
def dashboard_data():
    # TODO: Replace with real usage/balance from backend or database
    return jsonify({
        "username": current_user.code,
        "phone": current_user.phone,
        "data_balance": "800MB",
        "time_remaining": "2 hours 30 minutes",
        "status": "Active"
    })

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    phone = data.get('phone')
    package = data.get('package')
    amount = {"daily": 20, "weekly": 80, "monthly": 300}.get(package)
    if not phone or not amount:
        return jsonify(success=False, message="Invalid input"), 400
    mpesa_resp = initiate_stk_push(phone, amount, "WiFi", f"{package} package")
    # TODO: Insert logic to generate and send voucher upon payment confirmation
    return jsonify(success=True, message="STK Push sent", mpesa=mpesa_resp)

@app.route('/api/payment-callback', methods=['POST'])
def payment_callback():
    callback_data = request.get_json()
    print("Received M-Pesa callback:", callback_data)
    # TODO: Parse callback, verify payment success, generate and deliver voucher, update DB
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200

if __name__ == '__main__':
    app.run(debug=True)
