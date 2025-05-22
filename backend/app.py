# hotspot_project/settings.py

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'billing',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hotspot_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hotspot_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'wifi_billing.db',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'


# billing/models.py
from django.db import models

class Voucher(models.Model):
    code = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


# billing/views.py
import random
import string
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Voucher
from .utils.mpesa import initiate_stk_push

def home(request):
    return render(request, 'index.html')

def login_page(request):
    return render(request, 'login.html')

@login_required
def dashboard_page(request):
    return render(request, 'dashboard.html')

def pay_page(request):
    return render(request, 'pay.html')

@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        import json
        body = json.loads(request.body)
        code = body.get('voucher')
        voucher = Voucher.objects.filter(code=code, used=False).first()
        if voucher:
            voucher.used = True
            voucher.save()
            request.session['user'] = {'code': voucher.code, 'phone': voucher.phone}
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'message': 'Invalid or used voucher'})

@login_required
def api_logout(request):
    logout(request)
    return redirect('login_page')

@login_required
def api_dashboard(request):
    user = request.session.get('user')
    return JsonResponse({
        'username': user['code'],
        'phone': user['phone'],
        'data_balance': '800MB',
        'time_remaining': '2 hours 30 minutes',
        'status': 'Active'
    })

@csrf_exempt
def api_subscribe(request):
    import json
    body = json.loads(request.body)
    phone = body.get('phone')
    package = body.get('package')
    amount_map = {'daily': 20, 'weekly': 80, 'monthly': 300}
    amount = amount_map.get(package)
    if not phone or not amount:
        return JsonResponse({'success': False, 'message': 'Invalid input'}, status=400)
    request.session['pending_payment'] = {'phone': phone, 'package': package, 'amount': amount}
    mpesa_resp = initiate_stk_push(phone, amount, 'WiFi', f'{package} package')
    return JsonResponse({'success': True, 'message': 'STK Push sent', 'mpesa': mpesa_resp})

@csrf_exempt
def payment_callback(request):
    import json
    body = json.loads(request.body)
    try:
        body = body['Body']['stkCallback']
        result_code = body['ResultCode']
        if result_code != 0:
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})
        meta = {item['Name']: item['Value'] for item in body['CallbackMetadata']['Item']}
        phone = str(meta.get('PhoneNumber'))
        amount = int(meta.get('Amount'))
        if amount == 10:
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
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Invalid Amount'})
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        Voucher.objects.create(code=code, used=False, phone=phone)
        print(f"Send SMS to {phone}: Your Wi-Fi voucher code is {code}")
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})
    except Exception as e:
        print('Error processing callback:', e)
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Error'})


# billing/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_page, name='login_page'),
    path('dashboard/', views.dashboard_page, name='dashboard_page'),
    path('pay/', views.pay_page, name='pay_page'),
    path('api/login', views.api_login),
    path('api/logout', views.api_logout),
    path('api/dashboard', views.api_dashboard),
    path('api/subscribe', views.api_subscribe),
    path('api/payment-callback', views.payment_callback),
]


# hotspot_project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('billing.urls')),
]

