from django.urls import path
from . import views

urlpatterns = [
    path('api/subscribe/', views.stk_push_view, name='stk_push'),
]
