from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
import base64
import json
import requests
from datetime import datetime

# === Utilities ===
def get_access_token():
    url = f"{settings.MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET))
    return response.json().get('access_token')

def send_stk_push(phone, amount, account_ref, transaction_desc):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(
        f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()
    ).decode()

    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_ref,
        "TransactionDesc": transaction_desc
    }

    url = f"{settings.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# === Views ===
@csrf_exempt
def stk_push_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            phone = data.get('phone')
            package = data.get('package')

            packages = {
                "2hours": 10,
                "12hours": 20,
                "daily": 30,
                "weekly": 80,
                "monthly": 600,
            }

            if not phone or not package or package not in packages:
                return JsonResponse({"success": False, "message": "Invalid request."}, status=400)

            amount = packages[package]
            result = send_stk_push(phone, amount, f"{package}-WiFi", "WiFi package purchase")

            if result.get('ResponseCode') == '0':
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "message": result.get("errorMessage", "Failed to initiate payment.")})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid method."}, status=405)

# === URLConf ===
urlpatterns = [
    path('api/subscribe/', stk_push_view, name='stk_push'),
]

