import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .mpesa_utils import send_stk_push

@csrf_exempt
def stk_push_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            phone = data.get('phone')
            package = data.get('package')

            # Define package pricing
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
