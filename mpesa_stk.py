import os
import requests
import base64
import datetime
from dotenv import load_dotenv

load_dotenv()

def get_oauth_token():
    consumer_key = os.getenv('MPESA_CONSUMER_KEY')
    consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(consumer_key, consumer_secret))
    return response.json()['access_token']

def stk_push(phone, amount, account_reference, transaction_desc):
    access_token = get_oauth_token()
    business_short_code = os.getenv('MPESA_SHORTCODE')
    passkey = os.getenv('MPESA_PASSKEY')
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode((business_short_code + passkey + timestamp).encode()).decode()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "BusinessShortCode": business_short_code,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": business_short_code,
        "PhoneNumber": phone,
        "CallBackURL": os.getenv('MPESA_CALLBACK_URL'),
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc
    }
    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
