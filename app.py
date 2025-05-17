import os
from flask import Flask, request, jsonify
from mpesa_stk import stk_push
from mk_api import grant_access, revoke_access

app = Flask(__name__)

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    phone = data.get('phone')
    package = data.get('package')
    amount = {"daily": 20, "weekly": 80, "monthly": 300}.get(package)
    if not phone or not amount:
        return jsonify(success=False, message="Invalid input"), 400
    # Initiate M-Pesa STK Push
    mpesa_resp = stk_push(phone, amount, "WiFi", f"{package} package")
    # Save session to DB here in real app
    return jsonify(success=True, message="STK Push sent", mpesa=mpesa_resp)

@app.route('/api/payment-callback', methods=['POST'])
def payment_callback():
    # Parse Safaricom callback and verify success
    data = request.json
    # Parse phone, verify payment, then:
    phone = "0712345678"  # Replace with actual from callback
    grant_access(username=phone, password='defaultpass')
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

# Add auto-expiry logic as shown in previous answers

if __name__ == '__main__':
    app.run(debug=True)
