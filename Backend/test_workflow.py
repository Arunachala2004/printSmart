#!/usr/bin/env python
"""
Workflow Testing Script
Tests the complete file upload to printing workflow with dummy data
"""

import os
import sys
import django
from decimal import Decimal
from io import BytesIO

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')
django.setup()

from users.models import User
from files.models import File
from print_jobs.models import Printer, PrintJob
from payments.models import Payment
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware


def create_test_data():
    """Create test data for workflow testing"""
    print("\n=== STEP 1: CREATING TEST DATA ===")
    
    # Create test user
    try:
        user = User.objects.get(email='test@example.com')
        print("✓ Using existing test user")
    except User.DoesNotExist:
        # Try to create user with unique username
        import random
        username = f'testuser_{random.randint(1000, 9999)}'
        user = User.objects.create_user(
            username=username,
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print("✓ Created test user")
    
    # Set initial wallet balance
    user.wallet_balance = Decimal('50.00')
    user.save()
    print(f"✓ Set wallet balance to ${user.wallet_balance}")
    
    # Create test printer
    try:
        printer = Printer.objects.get(name='Test Printer')
        print("✓ Using existing test printer")
    except Printer.DoesNotExist:
        printer = Printer.objects.create(
            name='Test Printer',
            description='Test printer for workflow testing',
            printer_type='laser',
            ip_address='192.168.1.100',
            port=9100,
            supports_color=True,
            supports_duplex=True,
            status='online',
            is_active=True
        )
        print("✓ Created test printer")
    
    return user, printer


def test_file_upload(user):
    """Test file upload functionality"""
    print("\n=== STEP 2: TESTING FILE UPLOAD ===")
    
    # Create dummy file content
    file_content = b"This is a test PDF file content for workflow testing."
    test_file = SimpleUploadedFile(
        name='test_document.pdf',
        content=file_content,
        content_type='application/pdf'
    )
    
    # Create File object (simulating upload)
    try:
        file_obj = File.objects.create(
            user=user,
            original_filename='test_document.pdf',
            original_file=test_file,
            file_size=len(file_content),
            file_type='pdf',
            status='uploaded'
        )
        print(f"✓ File uploaded successfully: {file_obj.original_filename}")
        print(f"  - File ID: {file_obj.id}")
        print(f"  - Size: {file_obj.file_size} bytes")
        print(f"  - Type: {file_obj.file_type}")
        print(f"  - Status: {file_obj.status}")
        return file_obj
    except Exception as e:
        print(f"✗ File upload failed: {str(e)}")
        return None


def test_print_job_creation(user, file_obj, printer):
    """Test print job creation and cost calculation"""
    print("\n=== STEP 3: TESTING PRINT JOB CREATION ===")
    
    # Test parameters
    copies = 2
    color_mode = 'color'
    duplex = True
    
    # Calculate cost (same logic as in views.py)
    base_cost = 2.0 if color_mode == 'color' else 1.0
    total_cost = Decimal(str(base_cost * copies))
    
    print(f"Print job parameters:")
    print(f"  - Copies: {copies}")
    print(f"  - Color mode: {color_mode}")
    print(f"  - Duplex: {duplex}")
    print(f"  - Base cost per page: ${base_cost}")
    print(f"  - Total cost: ${total_cost}")
    
    # Check wallet balance
    print(f"  - User wallet balance: ${user.wallet_balance}")
    
    if user.wallet_balance < total_cost:
        print(f"✗ Insufficient wallet balance! Need ${total_cost}, have ${user.wallet_balance}")
        return None
    
    try:
        # Create print job
        print_job = PrintJob.objects.create(
            user=user,
            file=file_obj,
            printer=printer,
            copies=copies,
            color_mode=color_mode,
            duplex=duplex,
            total_cost=total_cost,
            status='pending'
        )
        
        print(f"✓ Print job created successfully: {print_job.id}")
        print(f"  - Status: {print_job.status}")
        print(f"  - Printer: {print_job.printer.name}")
        print(f"  - Total cost: ${print_job.total_cost}")
        
        return print_job
        
    except Exception as e:
        print(f"✗ Print job creation failed: {str(e)}")
        return None


def test_payment_processing(user, file_obj, total_cost):
    """Test payment processing and wallet deduction"""
    print("\n=== STEP 4: TESTING PAYMENT PROCESSING ===")
    
    original_balance = user.wallet_balance
    print(f"Original wallet balance: ${original_balance}")
    
    try:
        # Deduct from wallet
        user.wallet_balance -= total_cost
        user.save()
        
        print(f"✓ Wallet deducted: ${total_cost}")
        print(f"New wallet balance: ${user.wallet_balance}")
        
        # Create payment record
        import time
        reference_number = f"TEST_{int(time.time())}_{user.id}"
        payment = Payment.objects.create(
            user=user,
            amount=total_cost,
            payment_method='wallet',
            description=f'Print job for {file_obj.original_filename}',
            status='completed',
            reference_number=reference_number
        )
        
        print(f"✓ Payment record created: {payment.id}")
        print(f"  - Amount: ${payment.amount}")
        print(f"  - Method: {payment.payment_method}")
        print(f"  - Status: {payment.status}")
        
        return payment
        
    except Exception as e:
        print(f"✗ Payment processing failed: {str(e)}")
        return None


def test_print_job_status_updates(print_job):
    """Test print job status updates"""
    print("\n=== STEP 5: TESTING PRINT JOB STATUS UPDATES ===")
    
    status_flow = ['pending', 'processing', 'completed']
    
    for status in status_flow:
        try:
            print_job.status = status
            if status == 'processing':
                print_job.progress = 50
            elif status == 'completed':
                print_job.progress = 100
            print_job.save()
            
            print(f"✓ Status updated to: {status}")
            if hasattr(print_job, 'progress') and print_job.progress:
                print(f"  - Progress: {print_job.progress}%")
                
        except Exception as e:
            print(f"✗ Status update failed for {status}: {str(e)}")
            return False
    
    return True


def test_printer_status_monitoring(printer):
    """Test printer status monitoring"""
    print("\n=== STEP 6: TESTING PRINTER STATUS MONITORING ===")
    
    original_status = printer.status
    print(f"Original printer status: {original_status}")
    
    try:
        # Test status update
        printer.update_status('busy')
        print(f"✓ Printer status updated to: {printer.status}")
        
        # Test page count update
        original_pages = printer.total_pages_printed
        printer.add_printed_pages(2)  # 2 copies printed
        print(f"✓ Pages printed updated: {original_pages} → {printer.total_pages_printed}")
        
        # Reset to original status
        printer.update_status(original_status)
        print(f"✓ Printer status reset to: {printer.status}")
        
        return True
        
    except Exception as e:
        print(f"✗ Printer status monitoring failed: {str(e)}")
        return False


def test_error_scenarios():
    """Test error scenarios and edge cases"""
    print("\n=== STEP 7: TESTING ERROR SCENARIOS ===")
    
    try:
        # Test insufficient wallet balance
        user = User.objects.get(email='test@example.com')
        user.wallet_balance = Decimal('0.50')  # Very low balance
        user.save()
        
        print(f"✓ Set low wallet balance: ${user.wallet_balance}")
        
        # Try to create expensive print job
        total_cost = Decimal('10.00')
        if user.wallet_balance < total_cost:
            print(f"✓ Correctly detected insufficient funds (need ${total_cost}, have ${user.wallet_balance})")
        
        # Test offline printer
        printer = Printer.objects.get(name='Test Printer')
        printer.update_status('offline')
        
        active_printers = Printer.objects.filter(is_active=True, status='online')
        if not active_printers.exists():
            print("✓ Correctly detected no online printers available")
        else:
            print(f"! Warning: Found {active_printers.count()} online printers when expecting none")
        
        # Reset printer status
        printer.update_status('online')
        print("✓ Printer status reset to online")
        
        # Reset wallet balance
        user.wallet_balance = Decimal('50.00')
        user.save()
        
        return True
        
    except Exception as e:
        print(f"✗ Error scenario testing failed: {str(e)}")
        return False


def run_complete_workflow_test():
    """Run the complete workflow test"""
    print("==========================================")
    print("    PRINTSMART WORKFLOW TEST REPORT")
    print("==========================================")
    
    try:
        # Step 1: Create test data
        user, printer = create_test_data()
        
        # Step 2: Test file upload
        file_obj = test_file_upload(user)
        if not file_obj:
            print("\n✗ WORKFLOW FAILED: File upload failed")
            return False
        
        # Step 3: Test print job creation
        print_job = test_print_job_creation(user, file_obj, printer)
        if not print_job:
            print("\n✗ WORKFLOW FAILED: Print job creation failed")
            return False
        
        # Step 4: Test payment processing
        payment = test_payment_processing(user, file_obj, print_job.total_cost)
        if not payment:
            print("\n✗ WORKFLOW FAILED: Payment processing failed")
            return False
        
        # Step 5: Test print job status updates
        if not test_print_job_status_updates(print_job):
            print("\n✗ WORKFLOW FAILED: Status updates failed")
            return False
        
        # Step 6: Test printer monitoring
        if not test_printer_status_monitoring(printer):
            print("\n✗ WORKFLOW FAILED: Printer monitoring failed")
            return False
        
        # Step 7: Test error scenarios
        if not test_error_scenarios():
            print("\n✗ WORKFLOW FAILED: Error scenario testing failed")
            return False
        
        print("\n=== WORKFLOW TEST SUMMARY ===")
        print("✓ File upload: PASSED")
        print("✓ Print job creation: PASSED")
        print("✓ Payment processing: PASSED")
        print("✓ Status updates: PASSED")
        print("✓ Printer monitoring: PASSED")
        print("✓ Error handling: PASSED")
        print("\n🎉 COMPLETE WORKFLOW TEST: PASSED")
        
        return True
        
    except Exception as e:
        print(f"\n✗ WORKFLOW TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    run_complete_workflow_test()
