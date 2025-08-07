from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal
from .models import PrintJob
from files.models import File
from payments.models import Payment

@login_required
def job_list(request):
    """List all print jobs for the user"""
    jobs = PrintJob.objects.filter(user=request.user).order_by('-submitted_at')
    context = {
        'jobs': jobs,
        'total_jobs': jobs.count(),
        'pending_jobs': jobs.filter(status='pending').count(),
        'completed_jobs': jobs.filter(status='completed').count(),
    }
    return render(request, 'print_jobs/list.html', context)

@login_required
def job_detail(request, job_id):
    """View detailed information about a print job"""
    job = get_object_or_404(PrintJob, id=job_id, user=request.user)
    context = {
        'job': job,
    }
    return render(request, 'print_jobs/detail.html', context)

@login_required
def create_job(request):
    """Create a new print job"""
    if request.method == 'POST':
        file_id = request.POST.get('file_id')
        copies = request.POST.get('copies', 1)
        color_mode = request.POST.get('color_mode', 'bw')
        paper_size = request.POST.get('paper_size', 'A4')
        duplex = request.POST.get('duplex') == 'on'
        
        try:
            file_obj = get_object_or_404(File, id=file_id, user=request.user)
            copies = int(copies)
            
            # Calculate cost (simplified pricing)
            base_cost = Decimal('0.10')  # 10 cents per page
            if color_mode == 'color':
                base_cost = Decimal('0.25')  # 25 cents for color
            
            total_cost = base_cost * copies * file_obj.page_count
            
            # Check wallet balance
            if request.user.wallet_balance < total_cost:
                messages.error(request, 'Insufficient wallet balance. Please add money to your wallet.')
                return redirect('web:upload')
            
            # Create print job and process payment
            with transaction.atomic():
                job = PrintJob.objects.create(
                    user=request.user,
                    file=file_obj,
                    copies=copies,
                    color_mode=color_mode,
                    paper_size=paper_size,
                    duplex=duplex,
                    total_cost=total_cost,
                    status='pending'
                )
                
                # Create payment record
                Payment.objects.create(
                    user=request.user,
                    amount=total_cost,
                    payment_type='debit',
                    payment_method='wallet',
                    status='completed',
                    description=f'Print job #{job.id} - {file_obj.original_filename}'
                )
                
                # Update wallet balance
                request.user.wallet_balance -= total_cost
                request.user.save()
                
            messages.success(request, f'Print job created successfully! Cost: ${total_cost}')
            return redirect('print_jobs:detail', job_id=job.id)
            
        except Exception as e:
            messages.error(request, 'Failed to create print job. Please try again.')
            return redirect('web:upload')
    
    # GET request - show available files
    files = File.objects.filter(user=request.user)
    context = {
        'files': files,
    }
    return render(request, 'print_jobs/create.html', context)

@login_required
def cancel_job(request, job_id):
    """Cancel a print job"""
    job = get_object_or_404(PrintJob, id=job_id, user=request.user)
    
    if job.status != 'pending':
        messages.error(request, 'Only pending jobs can be cancelled.')
        return redirect('print_jobs:detail', job_id=job.id)
    
    try:
        with transaction.atomic():
            # Refund the amount
            Payment.objects.create(
                user=request.user,
                amount=job.total_cost,
                payment_type='credit',
                payment_method='wallet',
                status='completed',
                description=f'Refund for cancelled print job #{job.id}'
            )
            
            # Update wallet balance
            request.user.wallet_balance += job.total_cost
            request.user.save()
            
            # Update job status
            job.status = 'cancelled'
            job.save()
            
        messages.success(request, f'Print job cancelled and ${job.total_cost} refunded to your wallet.')
        
    except Exception as e:
        messages.error(request, 'Failed to cancel print job. Please try again.')
    
    return redirect('print_jobs:list')

@login_required
def job_status_update(request, job_id):
    """Update job status (for admin/system use)"""
    if request.method == 'POST':
        job = get_object_or_404(PrintJob, id=job_id)
        new_status = request.POST.get('status')
        
        if new_status in ['pending', 'processing', 'completed', 'cancelled']:
            job.status = new_status
            job.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Job status updated to {new_status}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})
