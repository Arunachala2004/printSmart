from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment history
    path('history/', views.payment_history, name='history'),
    
    # Wallet top-up with Razorpay
    path('wallet-topup/', views.wallet_topup_view, name='wallet_topup'),
    
    # Token packages and purchase
    path('tokens/', views.token_packages_view, name='token_packages'),
    path('tokens/purchase/<uuid:package_id>/', views.purchase_tokens, name='purchase_tokens'),
    
    # Razorpay payment handling
    path('payment-success/', views.payment_success_view, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('webhook/', views.razorpay_webhook, name='razorpay_webhook'),
    
    # Legacy endpoints (backward compatibility)
    path('add-money/', views.add_money, name='add_money'),
    path('process/', views.process_payment, name='process'),
]
