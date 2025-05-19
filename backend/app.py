import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from models import db, Voucher
from mpesa_stk import initiate_stk_push
import random, string

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
    # Save pending payment info (optional: to verify in callback)
    session['pending_payment'] = {'phone': phone, 'package': package, 'amount': amount}
    mpesa_resp = initiate_stk_push(phone, amount, "WiFi", f"{package} package")
    return jsonify(success=True, message="STK Push sent", mpesa=mpesa_resp)

@app.route('/api/payment-callback', methods=['POST'])
def payment_callback():
    callback_data = request.get_json()
    print("Received M-Pesa callback:", callback_data)

    # Parse result code and metadata
    try:
        body = callback_data['Body']['stkCallback']
        result_code = body['ResultCode']
        if result_code != 0:
            # Payment failed
            return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200

        # Extract details
        meta = {item['Name']: item['Value'] for item in body['CallbackMetadata']['Item']}
        phone = str(meta.get('PhoneNumber'))
        amount = int(meta.get('Amount'))

        # Determine the package bought (if saving pending payments, match here)
        # Example: match amount to package
        if amount ==10:
            package = '2 Hours'
        elif amount == 20:
            package = '24 Hours'
        elif amount == 80:
            package = 'weekly'
        elif amount == 600:
            package = 'monthly'
        else:
            package = 'unknown'
        if package == 'unknown':
            return jsonify({"ResultCode": 0, "ResultDesc": "Invalid Amount"}), 200

        # Generate and save voucher
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        voucher = Voucher(code=code, used=False, phone=phone)
        db.session.add(voucher)
        db.session.commit()

        # TODO: Send voucher via SMS (integrate with SMS gateway)
        print(f"Send SMS to {phone}: Your Wi-Fi voucher code is {code}")

        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200
    except Exception as e:
        print("Error processing callback:", e)
        return jsonify({"ResultCode": 0, "ResultDesc": "Error"}), 200

if __name__ == '__main__':
    app.run(debug=True)
