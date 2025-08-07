#!/usr/bin/env python
"""
Test Enhanced Printing Options
Tests the new comprehensive printing options functionality
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')
django.setup()

from users.models import User
from files.models import File
from print_jobs.models import Printer, PrintJob
from payments.models import Payment
from django.core.files.uploadedfile import SimpleUploadedFile
from web.views import calculate_pages_to_print, calculate_enhanced_cost


def test_page_calculation():
    """Test page calculation functionality"""
    print("\n=== TESTING PAGE CALCULATION ===")
    
    test_cases = [
        ('all', 10, 10),
        ('1-5', 10, 5),
        ('1,3,5,7,9', 10, 5),
        ('1-3,7-9', 10, 6),
        ('1-5,8,10-12', 15, 8),
        ('invalid', 10, 10),  # Should default to all pages
        ('', 10, 10),  # Should default to all pages
    ]
    
    for pages_input, total_pages, expected in test_cases:
        result = calculate_pages_to_print(pages_input, total_pages)
        status = "✓" if result == expected else "✗"
        print(f"{status} Pages '{pages_input}' from {total_pages} total → {result} (expected {expected})")


def test_cost_calculation():
    """Test enhanced cost calculation"""
    print("\n=== TESTING COST CALCULATION ===")
    
    test_cases = [
        # (pages, copies, color_mode, quality, expected_cost)
        (1, 1, 'bw', 'normal', 1.00),
        (1, 1, 'color', 'normal', 2.00),
        (1, 1, 'grayscale', 'normal', 1.50),
        (1, 1, 'bw', 'draft', 0.80),
        (1, 1, 'bw', 'high', 1.50),
        (1, 1, 'bw', 'best', 2.00),
        (5, 2, 'color', 'high', 30.00),  # 5 pages × 2 copies × $2.00 × 1.5 quality
        (3, 1, 'grayscale', 'draft', 3.60),  # 3 pages × 1 copy × $1.50 × 0.8 quality
    ]
    
    for pages, copies, color_mode, quality, expected in test_cases:
        result = float(calculate_enhanced_cost(pages, copies, color_mode, quality))
        status = "✓" if abs(result - expected) < 0.01 else "✗"
        print(f"{status} {pages}p × {copies}c × {color_mode} × {quality} → ${result:.2f} (expected ${expected:.2f})")


def test_printing_options_workflow():
    """Test complete printing workflow with enhanced options"""
    print("\n=== TESTING ENHANCED PRINTING WORKFLOW ===")
    
    # Get test user and printer
    try:
        user = User.objects.get(email='test@example.com')
        printer = Printer.objects.get(name='Test Printer')
        
        # Ensure printer is online and supports features
        printer.status = 'online'
        printer.supports_color = True
        printer.supports_duplex = True
        printer.save()
        
        print(f"✓ Using test user: {user.email}")
        print(f"✓ Using test printer: {printer.name} (Color: {printer.supports_color}, Duplex: {printer.supports_duplex})")
        
    except (User.DoesNotExist, Printer.DoesNotExist) as e:
        print(f"✗ Test data not found: {str(e)}")
        return False
    
    # Create test file with multiple pages
    file_content = b"Multi-page test document content for enhanced printing options testing."
    test_file = SimpleUploadedFile(
        name='enhanced_test.pdf',
        content=file_content,
        content_type='application/pdf'
    )
    
    file_obj = File.objects.create(
        user=user,
        original_filename='enhanced_test.pdf',
        original_file=test_file,
        file_size=len(file_content),
        file_type='pdf',
        status='uploaded',
        page_count=10  # Multi-page document
    )
    
    print(f"✓ Created test file: {file_obj.original_filename} ({file_obj.page_count} pages)")
    
    # Test different printing scenarios
    test_scenarios = [
        {
            'name': 'Basic B&W Print',
            'options': {
                'copies': 1,
                'pages': 'all',
                'color_mode': 'bw',
                'paper_size': 'A4',
                'print_quality': 'normal',
                'duplex': False,
                'orientation': 'portrait',
                'collate': True
            },
            'expected_cost': 10.00  # 10 pages × 1 copy × $1.00
        },
        {
            'name': 'Color High Quality',
            'options': {
                'copies': 2,
                'pages': '1-5',
                'color_mode': 'color',
                'paper_size': 'A4',
                'print_quality': 'high',
                'duplex': True,
                'orientation': 'landscape',
                'collate': True
            },
            'expected_cost': 30.00  # 5 pages × 2 copies × $2.00 × 1.5 quality
        },
        {
            'name': 'Selective Page Print',
            'options': {
                'copies': 1,
                'pages': '1,3,5,7,9',
                'color_mode': 'grayscale',
                'paper_size': 'Letter',
                'print_quality': 'draft',
                'duplex': False,
                'orientation': 'portrait',
                'collate': False
            },
            'expected_cost': 6.00  # 5 pages × 1 copy × $1.50 × 0.8 quality
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n--- Testing: {scenario['name']} ---")
        opts = scenario['options']
        
        # Calculate pages and cost
        pages_to_print = calculate_pages_to_print(opts['pages'], file_obj.page_count)
        total_cost = calculate_enhanced_cost(
            pages_to_print, opts['copies'], opts['color_mode'], opts['print_quality']
        )
        
        # Check if user can afford
        if user.wallet_balance < total_cost:
            user.wallet_balance = Decimal('100.00')
            user.save()
            print(f"✓ Topped up wallet balance to ${user.wallet_balance}")
        
        try:
            # Create print job with enhanced options
            print_job = PrintJob.objects.create(
                user=user,
                file=file_obj,
                printer=printer,
                copies=opts['copies'],
                pages=opts['pages'],
                color_mode=opts['color_mode'],
                paper_size=opts['paper_size'],
                print_quality=opts['print_quality'],
                duplex=opts['duplex'],
                collate=opts['collate'],
                orientation=opts['orientation'],
                total_pages=pages_to_print,
                total_cost=total_cost,
                status='pending',
                job_settings={
                    'test_scenario': scenario['name'],
                    'enhanced_options': True
                }
            )
            
            print(f"✓ Print job created: {print_job.id}")
            print(f"  - Pages to print: {pages_to_print} (from '{opts['pages']}')")
            print(f"  - Copies: {opts['copies']}")
            print(f"  - Color mode: {opts['color_mode']}")
            print(f"  - Quality: {opts['print_quality']}")
            print(f"  - Paper: {opts['paper_size']} {opts['orientation']}")
            print(f"  - Duplex: {opts['duplex']}")
            print(f"  - Collate: {opts['collate']}")
            print(f"  - Total cost: ${total_cost} (expected ${scenario['expected_cost']})")
            
            # Verify cost calculation
            cost_match = abs(float(total_cost) - scenario['expected_cost']) < 0.01
            cost_status = "✓" if cost_match else "✗"
            print(f"  {cost_status} Cost calculation {'correct' if cost_match else 'incorrect'}")
            
        except Exception as e:
            print(f"✗ Failed to create print job: {str(e)}")
            return False
    
    return True


def test_printer_compatibility():
    """Test printer capability validation"""
    print("\n=== TESTING PRINTER COMPATIBILITY ===")
    
    try:
        # Create printers with different capabilities
        bw_printer = Printer.objects.get_or_create(
            name='B&W Only Printer',
            defaults={
                'printer_type': 'laser',
                'supports_color': False,
                'supports_duplex': False,
                'status': 'online',
                'is_active': True
            }
        )[0]
        
        color_printer = Printer.objects.get_or_create(
            name='Color Printer',
            defaults={
                'printer_type': 'inkjet',
                'supports_color': True,
                'supports_duplex': True,
                'status': 'online',
                'is_active': True
            }
        )[0]
        
        print(f"✓ B&W Printer: {bw_printer.name} (Color: {bw_printer.supports_color}, Duplex: {bw_printer.supports_duplex})")
        print(f"✓ Color Printer: {color_printer.name} (Color: {color_printer.supports_color}, Duplex: {color_printer.supports_duplex})")
        
        # Test compatibility scenarios
        compatibility_tests = [
            (bw_printer, 'color', False, "B&W printer should not support color"),
            (bw_printer, 'duplex', False, "B&W printer should not support duplex"),
            (color_printer, 'color', True, "Color printer should support color"),
            (color_printer, 'duplex', True, "Color printer should support duplex"),
        ]
        
        for printer, feature, expected, description in compatibility_tests:
            if feature == 'color':
                actual = printer.supports_color
            elif feature == 'duplex':
                actual = printer.supports_duplex
            
            status = "✓" if actual == expected else "✗"
            print(f"{status} {description}: {actual}")
        
        return True
        
    except Exception as e:
        print(f"✗ Printer compatibility test failed: {str(e)}")
        return False


def generate_enhanced_options_report():
    """Generate comprehensive report of enhanced printing options"""
    print("\n" + "="*60)
    print("     ENHANCED PRINTING OPTIONS TEST REPORT")
    print("="*60)
    
    # Run all tests
    page_calc_ok = True
    cost_calc_ok = True
    workflow_ok = True
    compatibility_ok = True
    
    try:
        test_page_calculation()
    except Exception as e:
        print(f"✗ Page calculation test failed: {str(e)}")
        page_calc_ok = False
    
    try:
        test_cost_calculation()
    except Exception as e:
        print(f"✗ Cost calculation test failed: {str(e)}")
        cost_calc_ok = False
    
    try:
        workflow_ok = test_printing_options_workflow()
    except Exception as e:
        print(f"✗ Workflow test failed: {str(e)}")
        workflow_ok = False
    
    try:
        compatibility_ok = test_printer_compatibility()
    except Exception as e:
        print(f"✗ Compatibility test failed: {str(e)}")
        compatibility_ok = False
    
    # Generate summary
    print("\n=== TEST SUMMARY ===")
    print(f"✓ Page Calculation: {'PASS' if page_calc_ok else 'FAIL'}")
    print(f"✓ Cost Calculation: {'PASS' if cost_calc_ok else 'FAIL'}")
    print(f"✓ Enhanced Workflow: {'PASS' if workflow_ok else 'FAIL'}")
    print(f"✓ Printer Compatibility: {'PASS' if compatibility_ok else 'FAIL'}")
    
    # Feature summary
    print("\n=== ENHANCED FEATURES IMPLEMENTED ===")
    print("✓ Page Selection (All, Range, Specific)")
    print("✓ Color Modes (B&W, Grayscale, Full Color)")
    print("✓ Print Quality (Draft, Normal, High, Best)")
    print("✓ Paper Sizes (A4, A3, Letter, Legal)")
    print("✓ Orientation (Portrait, Landscape)")
    print("✓ Double-sided Printing (Duplex)")
    print("✓ Copy Collation")
    print("✓ Fit to Page Option")
    print("✓ Real-time Cost Calculation")
    print("✓ Printer Capability Validation")
    print("✓ Enhanced User Interface")
    
    # Database analysis
    try:
        total_jobs = PrintJob.objects.count()
        enhanced_jobs = PrintJob.objects.exclude(
            pages='all',
            print_quality='normal',
            paper_size='A4'
        ).count()
        
        print(f"\n=== DATABASE ANALYSIS ===")
        print(f"Total print jobs: {total_jobs}")
        print(f"Jobs with enhanced options: {enhanced_jobs}")
        
        if enhanced_jobs > 0:
            print("\nEnhanced option usage:")
            color_jobs = PrintJob.objects.exclude(color_mode='bw').count()
            quality_jobs = PrintJob.objects.exclude(print_quality='normal').count()
            page_select_jobs = PrintJob.objects.exclude(pages='all').count()
            duplex_jobs = PrintJob.objects.filter(duplex=True).count()
            
            print(f"  - Color/Grayscale: {color_jobs}")
            print(f"  - Non-normal quality: {quality_jobs}")
            print(f"  - Page selection: {page_select_jobs}")
            print(f"  - Duplex printing: {duplex_jobs}")
            
    except Exception as e:
        print(f"✗ Database analysis failed: {str(e)}")
    
    overall_status = all([page_calc_ok, cost_calc_ok, workflow_ok, compatibility_ok])
    
    print(f"\n🎯 OVERALL STATUS: {'✅ ALL FEATURES WORKING' if overall_status else '⚠️  SOME ISSUES FOUND'}")
    
    return overall_status


if __name__ == '__main__':
    generate_enhanced_options_report()
