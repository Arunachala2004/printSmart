from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('history/', views.payment_history, name='history'),
    path('add-money/', views.add_money, name='add_money'),
    path('process/', views.process_payment, name='process'),
]
