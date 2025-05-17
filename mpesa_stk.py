import os
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import base64

load_dotenv()

MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL")

def get_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET))
    access_token = response.json().get("access_token")
    return access_token

def initiate_stk_push(phone_number, amount, account_reference="Subscription", transaction_desc="Monthly Subscription"):
    access_token = get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data_to_encode = MPESA_SHORTCODE + MPESA_PASSKEY + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode()
    
    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": MPESA_CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
