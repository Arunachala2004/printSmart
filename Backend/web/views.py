from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import json

from users.models import User


def calculate_pages_to_print(pages_string, total_pages):
    """Calculate total pages to print from page specification"""
    if not pages_string or pages_string.strip() == '' or pages_string == 'all':
        return total_pages
    
    try:
        total_pages_to_print = 0
        parts = pages_string.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # Range like "1-5"
                start, end = part.split('-', 1)
                start = int(start.strip())
                end = int(end.strip())
                if start <= end <= total_pages:
                    total_pages_to_print += (end - start + 1)
            else:
                # Single page like "3"
                page = int(part.strip())
                if 1 <= page <= total_pages:
                    total_pages_to_print += 1
        
        return max(1, total_pages_to_print)
    except (ValueError, AttributeError):
        return total_pages  # Default to all pages if parsing fails


def calculate_enhanced_cost(pages_count, copies, color_mode, print_quality):
    """Calculate enhanced cost with all options"""
    # Base cost per page
    base_cost = Decimal('1.0')  # B&W
    if color_mode == 'grayscale':
        base_cost = Decimal('1.5')
    elif color_mode == 'color':
        base_cost = Decimal('2.0')
    
    # Quality multiplier
    quality_multipliers = {
        'draft': Decimal('0.8'),
        'normal': Decimal('1.0'),
        'high': Decimal('1.5'),
        'best': Decimal('2.0')
    }
    quality_multiplier = quality_multipliers.get(print_quality, Decimal('1.0'))
    
    # Calculate total cost
    total_cost = base_cost * pages_count * copies * quality_multiplier
    return total_cost.quantize(Decimal('0.01'))  # Round to 2 decimal places
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
    
    # Check if any printers are available
    if not printers.exists():
        messages.error(request, 'No printers are currently online. Please try again later or contact support.')
        return redirect('web:files')
    
    if request.method == 'POST':
        printer_id = request.POST.get('printer')
        copies = int(request.POST.get('copies', 1))
        color_mode = request.POST.get('color_mode', 'bw')
        duplex = request.POST.get('duplex') == 'on'
        
        # Enhanced printing options
        pages = request.POST.get('pages', 'all')
        page_selection = request.POST.get('page_selection', 'all')
        paper_size = request.POST.get('paper_size', 'A4')
        print_quality = request.POST.get('print_quality', 'normal')
        orientation = request.POST.get('orientation', 'portrait')
        collate = request.POST.get('collate') == 'on'
        fit_to_page = request.POST.get('fit_to_page') == 'on'
        
        # Process page selection
        if page_selection == 'all':
            pages = 'all'
        elif not pages or pages.strip() == '':
            pages = 'all'
        
        if not printer_id:
            messages.error(request, 'Please select a printer.')
            return redirect('web:print_file', file_id=file_id)
        
        printer = get_object_or_404(Printer, id=printer_id)
        
        # Critical: Re-check printer status before job submission
        if printer.status != 'online' or not printer.is_active:
            messages.error(request, f'Selected printer "{printer.name}" is currently {printer.status}. Please select a different printer.')
            return redirect('web:print_file', file_id=file_id)
        
        # Validate printer capabilities
        if color_mode in ['color', 'grayscale'] and not printer.supports_color:
            messages.error(request, f'Selected printer "{printer.name}" does not support color printing. Please select Black & White.')
            return redirect('web:print_file', file_id=file_id)
        
        if duplex and not printer.supports_duplex:
            messages.error(request, f'Selected printer "{printer.name}" does not support duplex printing.')
            return redirect('web:print_file', file_id=file_id)
        
        # Calculate total pages to print
        total_pages_to_print = calculate_pages_to_print(pages, file_obj.page_count or 1)
        
        # Enhanced cost calculation
        total_cost = calculate_enhanced_cost(
            pages_count=total_pages_to_print,
            copies=copies,
            color_mode=color_mode,
            print_quality=print_quality
        )
        
        # Check wallet balance
        if request.user.wallet_balance < total_cost:
            messages.error(request, 'Insufficient wallet balance. Please top up your wallet.')
            return redirect('web:wallet')
        
        try:
            with transaction.atomic():
                # Create enhanced print job
                print_job = PrintJob.objects.create(
                    user=request.user,
                    file=file_obj,
                    printer=printer,
                    copies=copies,
                    pages=pages,
                    color_mode=color_mode,
                    paper_size=paper_size,
                    print_quality=print_quality,
                    duplex=duplex,
                    collate=collate,
                    orientation=orientation,
                    total_pages=total_pages_to_print,
                    total_cost=total_cost,
                    status='pending',
                    # Store additional settings in job_settings JSON field
                    job_settings={
                        'fit_to_page': fit_to_page,
                        'page_selection_type': page_selection,
                        'original_page_count': file_obj.page_count or 1
                    }
                )
                
                # Deduct from wallet
                request.user.wallet_balance -= total_cost
                request.user.save()
                
                # Create payment record
                import time
                reference_number = f"PRINT_{int(time.time())}_{request.user.id}"
                Payment.objects.create(
                    user=request.user,
                    amount=total_cost,
                    payment_method='wallet',
                    description=f'Print job for {file_obj.original_filename}',
                    status='completed',
                    reference_number=reference_number
                )
            
            # Create detailed success message
            settings_summary = []
            if pages != 'all':
                settings_summary.append(f"Pages: {pages}")
            if copies > 1:
                settings_summary.append(f"{copies} copies")
            if color_mode != 'bw':
                settings_summary.append(f"{color_mode.replace('_', ' ').title()}")
            if print_quality != 'normal':
                settings_summary.append(f"{print_quality.title()} quality")
            if duplex:
                settings_summary.append("Double-sided")
            if orientation != 'portrait':
                settings_summary.append("Landscape")
            
            settings_text = f" ({', '.join(settings_summary)})" if settings_summary else ""
            
            messages.success(request, 
                f'Print job submitted successfully! Job ID: {print_job.id}'
                f'{settings_text}. Total cost: ${total_cost}'
            )
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
def select_printer(request, printer_id):
    """Select a printer for printing"""
    try:
        printer = Printer.objects.get(id=printer_id, is_active=True)
        # Store selected printer in session
        request.session['selected_printer_id'] = str(printer.id)
        messages.success(request, f'Printer "{printer.name}" selected successfully!')
        return redirect('web:files')
    except Printer.DoesNotExist:
        messages.error(request, 'Printer not found or not available.')
        return redirect('web:printers')


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
