from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from decimal import Decimal
from .models import Payment
from users.models import User
import uuid

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
def add_money(request):
    """Add money to wallet"""
    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method', 'card')
        
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                messages.error(request, 'Amount must be greater than 0')
                return redirect('web:wallet')
            
            # Create payment record
            with transaction.atomic():
                payment = Payment.objects.create(
                    user=request.user,
                    amount=amount,
                    payment_type='credit',
                    payment_method=payment_method,
                    status='completed',
                    description=f'Added money to wallet via {payment_method}'
                )
                
                # Update user wallet balance
                request.user.wallet_balance += amount
                request.user.save()
                
            messages.success(request, f'Successfully added ${amount} to your wallet!')
            
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount entered')
        except Exception as e:
            messages.error(request, 'Payment failed. Please try again.')
    
    return redirect('web:wallet')

@login_required
def process_payment(request):
    """Process payment for print jobs"""
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
