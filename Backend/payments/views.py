from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import razorpay  # type: ignore
import hmac
import hashlib
import json
import logging

from .models import Payment, TokenPackage, RazorpayOrder
from users.models import User

logger = logging.getLogger(__name__)

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def payment_history(request):
    """View payment history"""
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'payments': payments,
        'wallet_balance': request.user.wallet_balance,
    }
    return render(request, 'payments/history.html', context)

@login_required
def wallet_topup_view(request):
    """Wallet top-up with Razorpay"""
    if request.method == 'POST':
        try:
            amount = Decimal(str(request.POST.get('amount', 0)))
            
            if amount < 10:
                messages.error(request, 'Minimum top-up amount is ₹10')
                return redirect('web:wallet')
            
            if amount > 50000:
                messages.error(request, 'Maximum top-up amount is ₹50,000')
                return redirect('web:wallet')
            
            # Create Razorpay order
            # Use shorter receipt format to stay under 40 chars
            receipt = f'w{request.user.id}_{int(timezone.now().timestamp())}'[:40]
            razorpay_order = razorpay_client.order.create({
                'amount': int(amount * 100),  # Amount in paisa
                'currency': 'INR',
                'receipt': receipt,
                'notes': {
                    'user_id': str(request.user.id),
                    'type': 'wallet_topup'
                }
            })
            
            # Save order in database
            order = RazorpayOrder.objects.create(
                user=request.user,
                razorpay_order_id=razorpay_order['id'],
                amount=amount,
                order_type='wallet_topup'
            )
            
            context = {
                'razorpay_order_id': razorpay_order['id'],
                'amount': int(amount * 100),
                'amount_display': float(amount),  # Amount for display
                'currency': 'INR',
                'user_name': request.user.get_full_name() or request.user.username,
                'user_email': request.user.email,
                'user_phone': getattr(request.user, 'phone_number', ''),
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'order_id': str(order.id)
            }
            
            return render(request, 'payments/razorpay_payment.html', context)
            
        except Exception as e:
            logger.error(f"Error creating Razorpay order: {str(e)}")
            messages.error(request, 'Error processing payment. Please try again.')
            return redirect('web:wallet')
    
    return redirect('web:wallet')

@login_required
def token_packages_view(request):
    """View available token packages"""
    packages = TokenPackage.objects.filter(is_active=True).order_by('sort_order', 'price')
    
    # Calculate per-token price for each package
    for package in packages:
        package.per_token_price = round(float(package.price) / package.total_tokens, 2)
    
    context = {
        'packages': packages,
        'user_tokens': request.user.tokens,
        'wallet_balance': request.user.wallet_balance,
    }
    return render(request, 'payments/token_packages.html', context)

@login_required
def purchase_tokens(request, package_id):
    """Purchase tokens using Razorpay"""
    package = get_object_or_404(TokenPackage, id=package_id, is_active=True)
    
    # Calculate per-token price
    package.per_token_price = round(float(package.price) / package.total_tokens, 2)
    
    if request.method == 'POST':
        try:
            # Create Razorpay order
            # Use shorter receipt format to stay under 40 chars
            receipt = f't{request.user.id}_{int(timezone.now().timestamp())}'[:40]
            razorpay_order = razorpay_client.order.create({
                'amount': int(package.price * 100),  # Amount in paisa
                'currency': 'INR',
                'receipt': receipt,
                'notes': {
                    'user_id': str(request.user.id),
                    'package_id': str(package.id),
                    'type': 'token_purchase'
                }
            })
            
            # Save order in database
            order = RazorpayOrder.objects.create(
                user=request.user,
                razorpay_order_id=razorpay_order['id'],
                amount=package.price,
                order_type='token_purchase',
                token_package=package
            )
            
            context = {
                'razorpay_order_id': razorpay_order['id'],
                'amount': int(package.price * 100),
                'amount_display': float(package.price),  # Amount for display
                'currency': 'INR',
                'user_name': request.user.get_full_name() or request.user.username,
                'user_email': request.user.email,
                'user_phone': getattr(request.user, 'phone_number', ''),
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'order_id': str(order.id),
                'package': package
            }
            
            return render(request, 'payments/razorpay_payment.html', context)
            
        except Exception as e:
            logger.error(f"Error creating token purchase order: {str(e)}")
            messages.error(request, 'Error processing payment. Please try again.')
            return redirect('payments:token_packages')
    
    context = {
        'package': package,
    }
    return render(request, 'payments/purchase_tokens.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def payment_success(request):
    """Handle successful payment from Razorpay"""
    try:
        # Get payment details from request
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        order_id = request.POST.get('order_id')
        
        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature, order_id]):
            return JsonResponse({'success': False, 'message': 'Missing payment parameters'})
        
        # Verify payment signature
        generated_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != razorpay_signature:
            return JsonResponse({'success': False, 'message': 'Invalid payment signature'})
        
        # Get order and process payment
        order = get_object_or_404(RazorpayOrder, id=order_id)
        
        with transaction.atomic():
            # Update order status
            order.status = 'paid'
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.paid_at = timezone.now()
            order.save()
            
            # Process based on order type
            if order.order_type == 'wallet_topup':
                # Add money to wallet
                order.user.wallet_balance += order.amount
                order.user.save()
                
                # Create payment record
                Payment.objects.create(
                    user=order.user,
                    amount=order.amount,
                    payment_type='credit',
                    payment_method='razorpay',
                    status='completed',
                    description=f'Wallet top-up via Razorpay - {razorpay_payment_id}'
                )
                
                message = f'₹{order.amount} added to your wallet successfully!'
                
            elif order.order_type == 'token_purchase':
                # Add tokens to user account
                package = order.token_package
                order.user.tokens += package.total_tokens
                order.user.save()
                
                # Create payment record
                Payment.objects.create(
                    user=order.user,
                    amount=order.amount,
                    payment_type='debit',
                    payment_method='razorpay',
                    status='completed',
                    description=f'Token purchase - {package.name} ({package.total_tokens} tokens)'
                )
                
                message = f'Successfully purchased {package.total_tokens} tokens!'
            
            return JsonResponse({
                'success': True, 
                'message': message,
                'redirect_url': '/wallet/' if order.order_type == 'wallet_topup' else '/tokens/'
            })
            
    except Exception as e:
        logger.error(f"Payment success handling error: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error processing payment'})

@csrf_exempt
@require_http_methods(["POST"])
def payment_failed(request):
    """Handle failed payment from Razorpay"""
    try:
        razorpay_order_id = request.POST.get('razorpay_order_id')
        order_id = request.POST.get('order_id')
        error_description = request.POST.get('error_description', 'Payment failed')
        
        if order_id:
            # Update order status
            order = RazorpayOrder.objects.get(id=order_id)
            order.status = 'failed'
            order.save()
        
        return JsonResponse({
            'success': False,
            'message': error_description,
            'redirect_url': '/wallet/'
        })
        
    except Exception as e:
        logger.error(f"Payment failure handling error: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Payment failed'})

@csrf_exempt
@require_http_methods(["POST"])
def razorpay_webhook(request):
    """Handle Razorpay webhooks for payment updates"""
    try:
        # Verify webhook signature
        webhook_signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')
        webhook_body = request.body
        
        generated_signature = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode('utf-8'),
            webhook_body,
            hashlib.sha256
        ).hexdigest()
        
        if webhook_signature != generated_signature:
            logger.warning("Invalid webhook signature")
            return JsonResponse({'status': 'invalid signature'}, status=400)
        
        # Process webhook data
        webhook_data = json.loads(webhook_body)
        event = webhook_data.get('event')
        
        if event == 'payment.captured':
            # Handle successful payment
            payment_data = webhook_data['payload']['payment']['entity']
            order_id = payment_data['order_id']
            
            try:
                order = RazorpayOrder.objects.get(razorpay_order_id=order_id)
                if order.status != 'paid':
                    # Process the payment if not already processed
                    with transaction.atomic():
                        order.status = 'paid'
                        order.razorpay_payment_id = payment_data['id']
                        order.paid_at = timezone.now()
                        order.save()
                        
                        # Process payment based on type
                        # (Similar logic as payment_success view)
                        
            except RazorpayOrder.DoesNotExist:
                logger.warning(f"Order not found for webhook: {order_id}")
        
        elif event == 'payment.failed':
            # Handle failed payment
            payment_data = webhook_data['payload']['payment']['entity']
            order_id = payment_data['order_id']
            
            try:
                order = RazorpayOrder.objects.get(razorpay_order_id=order_id)
                order.status = 'failed'
                order.save()
            except RazorpayOrder.DoesNotExist:
                logger.warning(f"Order not found for failed payment webhook: {order_id}")
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return JsonResponse({'status': 'error'}, status=500)

# Legacy views (keeping for backward compatibility)
@login_required
def add_money(request):
    """Legacy add money view - redirects to Razorpay top-up"""
    if request.method == 'POST':
        return wallet_topup_view(request)
    return redirect('web:wallet')

@login_required
def process_payment(request):
    """Legacy process payment view"""
    if request.method == 'POST':
        amount = request.POST.get('amount')
        description = request.POST.get('description', 'Print job payment')
        
        try:
            amount = Decimal(str(amount))
            
            if request.user.wallet_balance < amount:
                return JsonResponse({
                    'success': False, 
                    'message': 'Insufficient wallet balance'
                })
            
            # Create payment record and deduct from wallet
            with transaction.atomic():
                payment = Payment.objects.create(
                    user=request.user,
                    amount=amount,
                    payment_type='debit',
                    payment_method='wallet',
                    status='completed',
                    description=description
                )
                
                # Update user wallet balance
                request.user.wallet_balance -= amount
                request.user.save()
                
            return JsonResponse({
                'success': True, 
                'message': 'Payment processed successfully',
                'new_balance': float(request.user.wallet_balance)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': 'Payment processing failed'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})
