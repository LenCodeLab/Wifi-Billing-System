import os
import base64
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === Utilities ===

def get_access_token():
    url = f"{os.getenv('MPESA_BASE_URL')}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(os.getenv('MPESA_CONSUMER_KEY'), os.getenv('MPESA_CONSUMER_SECRET')))
    return response.json().get('access_token')


def initiate_stk_push(phone, amount, account_ref, transaction_desc):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    passkey = os.getenv('MPESA_PASSKEY')
    shortcode = os.getenv('MPESA_SHORTCODE')

    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()

    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": os.getenv('MPESA_CALLBACK_URL'),
        "AccountReference": account_ref,
        "TransactionDesc": transaction_desc
    }

    url = f"{os.getenv('MPESA_BASE_URL')}/mpesa/stkpush/v1/processrequest"
    response = requests.post(url, json=payload, headers=headers)

    return response.json()


