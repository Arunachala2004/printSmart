from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from users.models import User
from files.models import File
from print_jobs.models import PrintJob, Printer
from payments.models import Payment


def home(request):
    """Home page - redirects to dashboard if logged in"""
    if request.user.is_authenticated:
        return redirect('web:dashboard')
    return render(request, 'web/home.html')


@login_required
def dashboard(request):
    """Main dashboard view"""
    user = request.user
    
    # Get user statistics
    total_files = File.objects.filter(user=user).count()
    total_print_jobs = PrintJob.objects.filter(user=user).count()
    print_jobs_completed = PrintJob.objects.filter(user=user, status='completed').count()
    print_jobs_pending = PrintJob.objects.filter(user=user, status='pending').count()
    wallet_balance = user.wallet_balance
    total_spent = Payment.objects.filter(
        user=user, 
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Get recent activity
    recent_print_jobs = PrintJob.objects.filter(user=user).order_by('-submitted_at')[:5]
    recent_files = File.objects.filter(user=user).order_by('-created_at')[:5]
    
    context = {
        'total_files': total_files,
        'total_print_jobs': total_print_jobs,
        'print_jobs_completed': print_jobs_completed,
        'print_jobs_pending': print_jobs_pending,
        'wallet_balance': wallet_balance,
        'pending_jobs': print_jobs_pending,
        'total_spent': total_spent,
        'recent_print_jobs': recent_print_jobs,
        'recent_files': recent_files,
    }
    return render(request, 'web/dashboard.html', context)


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('web:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next', 'web:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'web/auth/login.html')


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('web:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
        else:
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password1,
                    wallet_balance=100.00  # Welcome bonus
                )
                messages.success(request, 'Account created successfully! You can now login.')
                return redirect('web:login')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
    
    return render(request, 'web/auth/register.html')


@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('web:home')


@login_required
def files_view(request):
    if request.method == 'POST':
        try:
            if 'file' in request.FILES:
                uploaded_file = request.FILES['file']
                
                # Get file extension
                file_ext = uploaded_file.name.split('.')[-1].lower()
                
                # Create File object with correct fields
                file_obj = File.objects.create(
                    user=request.user,
                    original_file=uploaded_file,
                    original_filename=uploaded_file.name,
                    file_type=file_ext,
                    file_size=uploaded_file.size,
                    status='uploaded'
                )
                
                messages.success(request, f'File "{file_obj.original_filename}" uploaded successfully!')
                return redirect('web:files')
            else:
                messages.error(request, 'No file selected!')
        except Exception as e:
            messages.error(request, f'Upload failed: {str(e)}')
    
    files = File.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'files': files,
        'total_files': files.count(),
    }
    return render(request, 'web/files.html', context)


@login_required
def file_detail_view(request, file_id):
    """File detail view"""
    file_obj = get_object_or_404(File, id=file_id, user=request.user)
    
    # Get print jobs for this file
    print_jobs = PrintJob.objects.filter(file=file_obj).order_by('-submitted_at')
    
    context = {
        'file': file_obj,
        'print_jobs': print_jobs,
    }
    return render(request, 'web/file_detail.html', context)


@login_required
def upload_file_view(request):
    """File upload view"""
    if request.method == 'POST':
        try:
            if 'file' not in request.FILES:
                messages.error(request, 'No file selected.')
                return redirect('web:upload_file')
            
            uploaded_file = request.FILES['file']
            
            # Basic file validation
            if uploaded_file.size > 50 * 1024 * 1024:  # 50MB limit
                messages.error(request, 'File size too large. Maximum 50MB allowed.')
                return redirect('web:upload_file')
            
            # Get file extension
            file_ext = uploaded_file.name.split('.')[-1].lower()
            
            file_obj = File.objects.create(
                user=request.user,
                original_file=uploaded_file,
                original_filename=uploaded_file.name,
                file_type=file_ext,
                file_size=uploaded_file.size,
                status='uploaded'
            )
            messages.success(request, f'File "{file_obj.original_filename}" uploaded successfully!')
            return redirect('web:files')
        except Exception as e:
            messages.error(request, f'Error uploading file: {str(e)}')
    
    return render(request, 'web/upload_file.html')


@login_required
def print_file_view(request, file_id):
    """Print file submission view"""
    file_obj = get_object_or_404(File, id=file_id, user=request.user)
    printers = Printer.objects.filter(is_active=True, status='online')
    
    if request.method == 'POST':
        printer_id = request.POST.get('printer')
        copies = int(request.POST.get('copies', 1))
        color_mode = request.POST.get('color_mode', 'bw')
        duplex = request.POST.get('duplex') == 'on'
        
        if not printer_id:
            messages.error(request, 'Please select a printer.')
            return redirect('web:print_file', file_id=file_id)
        
        printer = get_object_or_404(Printer, id=printer_id)
        
        # Calculate cost (simplified)
        base_cost = 2.0 if color_mode == 'color' else 1.0
        total_cost = base_cost * copies
        
        # Check wallet balance
        if request.user.wallet_balance < total_cost:
            messages.error(request, 'Insufficient wallet balance. Please top up your wallet.')
            return redirect('web:wallet')
        
        try:
            # Create print job
            print_job = PrintJob.objects.create(
                user=request.user,
                file=file_obj,
                printer=printer,
                copies=copies,
                color_mode=color_mode,
                duplex=duplex,
                total_cost=total_cost,
                status='pending'
            )
            
            # Deduct from wallet
            request.user.wallet_balance -= total_cost
            request.user.save()
            
            # Create payment record
            Payment.objects.create(
                user=request.user,
                amount=total_cost,
                payment_method='wallet',
                description=f'Print job for {file_obj.original_filename}',
                status='completed'
            )
            
            messages.success(request, f'Print job submitted successfully! Job ID: {print_job.id}')
            return redirect('web:print_jobs')
            
        except Exception as e:
            messages.error(request, f'Error submitting print job: {str(e)}')
    
    context = {
        'file': file_obj,
        'printers': printers,
    }
    return render(request, 'web/print_file.html', context)


@login_required
def print_jobs_view(request):
    """Print jobs view"""
    user_print_jobs = PrintJob.objects.filter(user=request.user)
    print_jobs = user_print_jobs.order_by('-submitted_at')
    
    # Statistics
    total_jobs = user_print_jobs.count()
    completed_jobs = user_print_jobs.filter(status='completed').count()
    pending_jobs = user_print_jobs.filter(status='pending').count()
    failed_jobs = user_print_jobs.filter(status='failed').count()
    
    # Pagination
    paginator = Paginator(print_jobs, 10)
    page_number = request.GET.get('page')
    print_jobs = paginator.get_page(page_number)
    
    context = {
        'print_jobs': print_jobs,
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'pending_jobs': pending_jobs,
        'failed_jobs': failed_jobs,
    }
    return render(request, 'web/print_jobs.html', context)


@login_required
def wallet_view(request):
    """Wallet management view"""
    # Get user's payment history
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    payments = paginator.get_page(page_number)
    
    context = {
        'payments': payments,
    }
    return render(request, 'web/wallet.html', context)


@login_required
@require_http_methods(["POST"])
def add_money(request):
    """Add money to wallet"""
    try:
        amount = float(request.POST.get('amount', 0))
        payment_method = request.POST.get('payment_method', '')
        
        if amount < 10:
            messages.error(request, 'Minimum amount is ₹10')
            return redirect('web:wallet')
        
        if amount > 10000:
            messages.error(request, 'Maximum amount is ₹10,000')
            return redirect('web:wallet')
        
        if not payment_method:
            messages.error(request, 'Please select a payment method')
            return redirect('web:wallet')
        
        # Add money to wallet
        request.user.wallet_balance += amount
        request.user.save()
        
        # Create payment record
        Payment.objects.create(
            user=request.user,
            amount=amount,
            payment_method=payment_method,
            description=f'Wallet top-up via {payment_method.upper()}',
            status='completed'
        )
        
        messages.success(request, f'₹{amount:.2f} added to your wallet successfully!')
        
    except ValueError:
        messages.error(request, 'Invalid amount entered')
    except Exception as e:
        messages.error(request, f'Error processing payment: {str(e)}')
    
    return redirect('web:wallet')


@login_required
def printers_view(request):
    """View available printers"""
    printers = Printer.objects.filter(is_active=True).order_by('name')
    
    # Get printer statistics
    total_printers = printers.count()
    online_printers = printers.filter(status='online').count()
    busy_printers = printers.filter(status='busy').count()
    offline_printers = printers.filter(status='offline').count()
    
    # Add queue count for each printer
    for printer in printers:
        printer.queue_count = PrintJob.objects.filter(
            printer=printer, 
            status__in=['pending', 'processing']
        ).count()
    
    context = {
        'printers': printers,
        'total_printers': total_printers,
        'online_printers': online_printers,
        'busy_printers': busy_printers,
        'offline_printers': offline_printers,
    }
    return render(request, 'web/printers.html', context)


@login_required
def profile_view(request):
    """User profile view"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        
        # Update user profile
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.phone_number = phone_number
        request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('web:profile')
    
    return render(request, 'web/profile.html')


@login_required
@require_http_methods(["POST"])
def delete_file_view(request, file_id):
    """Delete a file"""
    file_obj = get_object_or_404(File, id=file_id, user=request.user)
    file_name = file_obj.original_filename
    
    try:
        file_obj.delete()
        messages.success(request, f'File "{file_name}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting file: {str(e)}')
    
    return redirect('web:files')


@login_required
@require_http_methods(["POST"])
def cancel_print_job(request, job_id):
    """Cancel a print job"""
    try:
        job = get_object_or_404(PrintJob, id=job_id, user=request.user)
        
        if job.status == 'pending':
            job.status = 'cancelled'
            job.save()
            
            # Refund to wallet
            request.user.wallet_balance += job.total_cost
            request.user.save()
            
            # Create refund payment record
            Payment.objects.create(
                user=request.user,
                amount=job.total_cost,
                payment_method='wallet',
                description=f'Refund for cancelled print job',
                status='completed'
            )
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Cannot cancel this job'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def admin_dashboard(request):
    """Admin dashboard (staff only)"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('web:dashboard')
    
    # Get admin statistics
    total_users = User.objects.count()
    total_files = File.objects.count()
    total_jobs = PrintJob.objects.count()
    pending_jobs = PrintJob.objects.filter(status='pending').count()
    
    # Recent activity
    recent_jobs = PrintJob.objects.all().order_by('-submitted_at')[:10]
    recent_users = User.objects.filter(is_active=True).order_by('-date_joined')[:5]
    
    context = {
        'total_users': total_users,
        'total_files': total_files,
        'total_jobs': total_jobs,
        'pending_jobs': pending_jobs,
        'recent_jobs': recent_jobs,
        'recent_users': recent_users,
    }
    return render(request, 'web/admin/dashboard.html', context)
