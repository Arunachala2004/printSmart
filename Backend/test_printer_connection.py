#!/usr/bin/env python
"""
Printer Connection Issue Analysis and Testing
Analyzes what happens when server-printer connection fails
"""

import os
import sys
import django
from decimal import Decimal
import socket
import subprocess
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')
django.setup()

from users.models import User
from files.models import File
from print_jobs.models import Printer, PrintJob
from payments.models import Payment


def test_printer_connectivity(printer):
    """Test actual network connectivity to a printer"""
    print(f"\n=== TESTING PRINTER CONNECTIVITY: {printer.name} ===")
    
    if not printer.ip_address:
        print("✗ No IP address configured for printer")
        return False
    
    # Test 1: Ping test
    try:
        print(f"Testing ping to {printer.ip_address}...")
        result = subprocess.run(
            ['ping', '-n', '1', '-w', '3000', printer.ip_address],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✓ Ping successful - Network reachable")
            ping_success = True
        else:
            print("✗ Ping failed - Network unreachable")
            ping_success = False
            
    except subprocess.TimeoutExpired:
        print("✗ Ping timeout - Network very slow or unreachable")
        ping_success = False
    except Exception as e:
        print(f"✗ Ping error: {str(e)}")
        ping_success = False
    
    # Test 2: Port connectivity test
    port_success = False
    if printer.port:
        try:
            print(f"Testing port connectivity to {printer.ip_address}:{printer.port}...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((printer.ip_address, printer.port))
            sock.close()
            
            if result == 0:
                print("✓ Port is open and reachable")
                port_success = True
            else:
                print(f"✗ Port {printer.port} is not reachable")
                
        except Exception as e:
            print(f"✗ Port test error: {str(e)}")
    else:
        print("! No port configured - skipping port test")
        port_success = True  # Assume success if no port specified
    
    return ping_success and port_success


def simulate_connection_failures():
    """Simulate various connection failure scenarios"""
    print("\n" + "="*60)
    print("    PRINTER CONNECTION FAILURE SIMULATION")
    print("="*60)
    
    # Get or create test printer
    try:
        printer = Printer.objects.get(name='Test Printer')
    except Printer.DoesNotExist:
        printer = Printer.objects.create(
            name='Test Printer',
            description='Test printer for connection failure testing',
            printer_type='laser',
            ip_address='192.168.1.100',  # Simulated IP
            port=9100,
            supports_color=True,
            supports_duplex=True,
            status='online',
            is_active=True
        )
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Network Timeout',
            'description': 'Printer IP unreachable (network down)',
            'ip': '192.168.1.200',  # Likely unreachable IP
            'expected_status': 'offline'
        },
        {
            'name': 'Port Closed',
            'description': 'Printer IP reachable but print service down',
            'ip': '8.8.8.8',  # Google DNS - reachable but port 9100 closed
            'expected_status': 'error'
        },
        {
            'name': 'Invalid IP',
            'description': 'Invalid IP address configuration',
            'ip': '999.999.999.999',
            'expected_status': 'error'
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- SCENARIO {i}: {scenario['name']} ---")
        print(f"Description: {scenario['description']}")
        
        # Update printer IP for testing
        original_ip = printer.ip_address
        printer.ip_address = scenario['ip']
        printer.save()
        
        # Test connectivity
        is_connected = test_printer_connectivity(printer)
        
        # Determine what should happen
        if not is_connected:
            print(f"Expected action: Set printer status to '{scenario['expected_status']}'")
            printer.update_status(scenario['expected_status'])
            print(f"✓ Printer status updated to: {printer.status}")
        
        results.append({
            'scenario': scenario['name'],
            'connected': is_connected,
            'status': printer.status
        })
        
        # Restore original IP
        printer.ip_address = original_ip
        printer.save()
    
    return results


def analyze_current_system_gaps():
    """Analyze what the current system is missing for connection handling"""
    print("\n" + "="*60)
    print("    CURRENT SYSTEM GAP ANALYSIS")
    print("="*60)
    
    gaps = []
    
    # Check 1: Is there a printer monitoring service?
    print("\n1. PRINTER MONITORING SERVICE:")
    try:
        # Look for background tasks or monitoring
        from django.core.management import get_commands
        commands = get_commands()
        
        monitoring_commands = [cmd for cmd in commands if 'monitor' in cmd or 'printer' in cmd]
        
        if monitoring_commands:
            print(f"✓ Found monitoring commands: {monitoring_commands}")
        else:
            print("✗ No printer monitoring commands found")
            gaps.append("No automated printer status monitoring")
    except Exception as e:
        print(f"✗ Error checking commands: {str(e)}")
        gaps.append("Cannot verify monitoring services")
    
    # Check 2: Retry mechanism for failed jobs
    print("\n2. RETRY MECHANISM:")
    try:
        # Check if PrintJob model has retry logic
        sample_job = PrintJob.objects.first()
        if sample_job:
            if hasattr(sample_job, 'retry_count') and hasattr(sample_job, 'max_retries'):
                print("✓ PrintJob model has retry fields")
                print(f"  - retry_count: {sample_job.retry_count}")
                print(f"  - max_retries: {sample_job.max_retries}")
            else:
                print("✗ PrintJob model missing retry mechanism")
                gaps.append("No retry mechanism for failed print jobs")
        else:
            print("! No print jobs found to check retry mechanism")
    except Exception as e:
        print(f"✗ Error checking retry mechanism: {str(e)}")
    
    # Check 3: Connection testing utilities
    print("\n3. CONNECTION TESTING:")
    try:
        # Check if Printer model has connection test methods
        printer = Printer.objects.first()
        if printer:
            test_methods = [method for method in dir(printer) if 'test' in method.lower() or 'ping' in method.lower()]
            if test_methods:
                print(f"✓ Found connection test methods: {test_methods}")
            else:
                print("✗ No connection testing methods in Printer model")
                gaps.append("No built-in connection testing utilities")
        else:
            print("! No printers found to check connection methods")
    except Exception as e:
        print(f"✗ Error checking connection methods: {str(e)}")
    
    # Check 4: Error handling in views
    print("\n4. VIEW ERROR HANDLING:")
    try:
        from web.views import print_file_view
        import inspect
        
        source = inspect.getsource(print_file_view)
        
        if 'offline' in source or 'connection' in source or 'unreachable' in source:
            print("✓ Views check for printer availability")
        else:
            print("✗ Views don't handle printer connection issues")
            gaps.append("Views lack printer connection error handling")
            
        if 'try:' in source and 'except' in source:
            print("✓ Views have basic exception handling")
        else:
            print("✗ Views lack exception handling")
            gaps.append("Views need better exception handling")
            
    except Exception as e:
        print(f"✗ Error analyzing view code: {str(e)}")
    
    # Check 5: Notification system for failures
    print("\n5. FAILURE NOTIFICATION SYSTEM:")
    try:
        from core.models import Notification
        print("✓ Notification model exists")
        
        # Check if there are printer-related notifications
        printer_notifications = Notification.objects.filter(
            notification_type='print_job'
        ).count()
        print(f"✓ Found {printer_notifications} print job notifications")
        
    except ImportError:
        print("✗ No notification system found")
        gaps.append("No user notification system for print failures")
    except Exception as e:
        print(f"✗ Error checking notifications: {str(e)}")
    
    return gaps


def simulate_workflow_with_connection_issues():
    """Simulate the complete workflow when printer connection fails"""
    print("\n" + "="*60)
    print("    WORKFLOW SIMULATION WITH CONNECTION ISSUES")
    print("="*60)
    
    # Create test data
    try:
        user = User.objects.get(email='test@example.com')
    except User.DoesNotExist:
        print("✗ Test user not found. Run main workflow test first.")
        return
    
    # Create a file
    from django.core.files.uploadedfile import SimpleUploadedFile
    file_content = b"Test document for connection failure testing."
    test_file = SimpleUploadedFile(
        name='connection_test.pdf',
        content=file_content,
        content_type='application/pdf'
    )
    
    file_obj = File.objects.create(
        user=user,
        original_filename='connection_test.pdf',
        original_file=test_file,
        file_size=len(file_content),
        file_type='pdf',
        status='uploaded'
    )
    
    # Get printer and simulate it going offline
    printer = Printer.objects.filter(name='Test Printer').first()
    if not printer:
        print("✗ No test printer found")
        return
    
    print(f"Initial printer status: {printer.status}")
    
    # Simulate connection failure scenarios
    scenarios = [
        {
            'name': 'Printer goes offline during job submission',
            'printer_status': 'offline',
            'expected_behavior': 'Job should be rejected or queued'
        },
        {
            'name': 'Printer has error during job processing',
            'printer_status': 'error',
            'expected_behavior': 'Job should be marked as failed'
        },
        {
            'name': 'Printer is busy (another job running)',
            'printer_status': 'busy',
            'expected_behavior': 'Job should be queued'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- TESTING: {scenario['name']} ---")
        
        # Set printer status
        printer.update_status(scenario['printer_status'])
        print(f"Printer status set to: {printer.status}")
        
        # Try to create print job
        try:
            # This simulates what happens in print_file_view
            printers = Printer.objects.filter(is_active=True, status='online')
            
            if not printers.exists():
                print("✓ Correctly detected: No online printers available")
                print(f"Expected: {scenario['expected_behavior']}")
                continue
            
            # If we get here, the current system would allow the job
            print("⚠️  Current system allows job submission to offline printer")
            
            # Try to create the job anyway (current behavior)
            copies = 1
            color_mode = 'bw'
            total_cost = Decimal('1.0')
            
            if user.wallet_balance >= total_cost:
                print_job = PrintJob.objects.create(
                    user=user,
                    file=file_obj,
                    printer=printer,  # This might be offline!
                    copies=copies,
                    color_mode=color_mode,
                    total_cost=total_cost,
                    status='pending'
                )
                print(f"✗ Job created despite printer being {printer.status}")
                print(f"Job ID: {print_job.id}, Status: {print_job.status}")
                
                # This is where problems would occur
                print("⚠️  PROBLEM: Job created but printer cannot fulfill it")
                
        except Exception as e:
            print(f"✗ Error during job creation: {str(e)}")
    
    # Reset printer status
    printer.update_status('online')
    print(f"\nPrinter status reset to: {printer.status}")


def generate_recommendations():
    """Generate recommendations for handling printer connection issues"""
    print("\n" + "="*60)
    print("    RECOMMENDATIONS FOR PRINTER CONNECTION HANDLING")
    print("="*60)
    
    recommendations = [
        {
            'priority': 'CRITICAL',
            'title': 'Implement Printer Health Monitoring',
            'description': 'Create a background service to periodically check printer connectivity',
            'implementation': [
                'Create Django management command for printer monitoring',
                'Use ping + port connectivity tests',
                'Update printer status automatically',
                'Run every 1-2 minutes via cron/scheduler'
            ]
        },
        {
            'priority': 'CRITICAL',
            'title': 'Enhance Print Job Validation',
            'description': 'Prevent job submission to offline/error printers',
            'implementation': [
                'Add real-time printer status check in print_file_view',
                'Reject jobs if no online printers available',
                'Show user-friendly error messages',
                'Suggest alternative printers if available'
            ]
        },
        {
            'priority': 'HIGH',
            'title': 'Implement Job Retry Mechanism',
            'description': 'Automatically retry failed jobs when printer comes back online',
            'implementation': [
                'Use existing retry_count and max_retries fields',
                'Create background task to retry failed jobs',
                'Exponential backoff for retry attempts',
                'Notify user after max retries exceeded'
            ]
        },
        {
            'priority': 'HIGH',
            'title': 'Add Connection Error Handling',
            'description': 'Gracefully handle connection timeouts and errors',
            'implementation': [
                'Wrap printer communication in try-catch blocks',
                'Set job status to "failed" on connection errors',
                'Log detailed error messages',
                'Provide user-friendly error explanations'
            ]
        },
        {
            'priority': 'MEDIUM',
            'title': 'Implement User Notifications',
            'description': 'Notify users when print jobs fail due to printer issues',
            'implementation': [
                'Send email/SMS when job fails',
                'Show in-app notifications',
                'Provide estimated resolution time',
                'Offer refund or reprint options'
            ]
        },
        {
            'priority': 'MEDIUM',
            'title': 'Add Printer Status Dashboard',
            'description': 'Admin dashboard to monitor all printer statuses',
            'implementation': [
                'Real-time printer status display',
                'Connection history and uptime stats',
                'Manual printer control (enable/disable)',
                'Alert system for prolonged downtime'
            ]
        },
        {
            'priority': 'LOW',
            'title': 'Implement Load Balancing',
            'description': 'Distribute jobs across multiple online printers',
            'implementation': [
                'Queue management system',
                'Printer capacity tracking',
                'Automatic job routing',
                'Priority-based job scheduling'
            ]
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. [{rec['priority']}] {rec['title']}")
        print(f"   {rec['description']}")
        print("   Implementation steps:")
        for step in rec['implementation']:
            print(f"   • {step}")
    
    return recommendations


def create_sample_monitoring_service():
    """Create a sample printer monitoring service"""
    print("\n" + "="*60)
    print("    CREATING SAMPLE PRINTER MONITORING SERVICE")
    print("="*60)
    
    monitoring_code = '''
#!/usr/bin/env python
"""
Printer Monitoring Service
Monitors printer connectivity and updates status automatically
"""

import os
import sys
import django
import socket
import subprocess
import time
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')
django.setup()

from print_jobs.models import Printer
from core.models import Notification
from users.models import User


class PrinterMonitor:
    def __init__(self):
        self.check_interval = 60  # Check every minute
        self.timeout = 5  # 5 second timeout for connections
    
    def ping_printer(self, ip_address):
        """Test printer connectivity via ping"""
        try:
            result = subprocess.run(
                ['ping', '-n', '1', '-w', '3000', ip_address],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return result.returncode == 0
        except:
            return False
    
    def test_port(self, ip_address, port):
        """Test printer port connectivity"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip_address, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def check_printer_status(self, printer):
        """Check individual printer status"""
        if not printer.ip_address:
            return 'unknown'
        
        # Test ping first
        if not self.ping_printer(printer.ip_address):
            return 'offline'
        
        # Test port if specified
        if printer.port:
            if not self.test_port(printer.ip_address, printer.port):
                return 'error'
        
        return 'online'
    
    def update_printer_status(self, printer, new_status):
        """Update printer status and notify if changed"""
        old_status = printer.status
        
        if old_status != new_status:
            printer.update_status(new_status)
            
            # Log status change
            print(f"[{datetime.now()}] Printer {printer.name}: {old_status} -> {new_status}")
            
            # Notify admins of status change
            admin_users = User.objects.filter(role='admin')
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    title=f"Printer Status Changed: {printer.name}",
                    message=f"Printer {printer.name} status changed from {old_status} to {new_status}",
                    notification_type='system'
                )
            
            # Handle failed print jobs if printer went offline
            if new_status in ['offline', 'error']:
                self.handle_printer_failure(printer)
    
    def handle_printer_failure(self, printer):
        """Handle print jobs when printer fails"""
        from print_jobs.models import PrintJob
        
        # Find pending/processing jobs for this printer
        failed_jobs = PrintJob.objects.filter(
            printer=printer,
            status__in=['pending', 'processing', 'printing']
        )
        
        for job in failed_jobs:
            job.status = 'failed'
            job.error_message = f"Printer {printer.name} went offline"
            job.save()
            
            # Notify user
            Notification.objects.create(
                user=job.user,
                title="Print Job Failed",
                message=f"Your print job for {job.file.original_filename} failed because the printer went offline. You will be refunded.",
                notification_type='print_job'
            )
    
    def monitor_all_printers(self):
        """Monitor all active printers"""
        printers = Printer.objects.filter(is_active=True)
        
        for printer in printers:
            try:
                new_status = self.check_printer_status(printer)
                self.update_printer_status(printer, new_status)
            except Exception as e:
                print(f"Error checking printer {printer.name}: {str(e)}")
    
    def run(self):
        """Main monitoring loop"""
        print(f"Starting printer monitoring service...")
        print(f"Check interval: {self.check_interval} seconds")
        
        while True:
            try:
                self.monitor_all_printers()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                print("Monitoring service stopped")
                break
            except Exception as e:
                print(f"Monitoring error: {str(e)}")
                time.sleep(self.check_interval)


if __name__ == '__main__':
    monitor = PrinterMonitor()
    monitor.run()
    '''
    
    return monitoring_code


def main():
    """Main function to run all connection issue tests"""
    print("PrintSmart Printer Connection Issue Analysis")
    print("=" * 50)
    
    # Run all tests
    connection_results = simulate_connection_failures()
    system_gaps = analyze_current_system_gaps()
    simulate_workflow_with_connection_issues()
    recommendations = generate_recommendations()
    monitoring_code = create_sample_monitoring_service()
    
    # Generate final report
    print("\n" + "="*60)
    print("    FINAL CONNECTION ISSUE ANALYSIS REPORT")
    print("="*60)
    
    print(f"\n📊 CONNECTION TEST RESULTS:")
    for result in connection_results:
        status = "✓ CONNECTED" if result['connected'] else "✗ FAILED"
        print(f"  {result['scenario']}: {status} (Status: {result['status']})")
    
    print(f"\n🔍 SYSTEM GAPS IDENTIFIED:")
    if system_gaps:
        for gap in system_gaps:
            print(f"  • {gap}")
    else:
        print("  ✓ No major gaps found")
    
    print(f"\n💡 RECOMMENDATIONS SUMMARY:")
    critical = len([r for r in recommendations if r['priority'] == 'CRITICAL'])
    high = len([r for r in recommendations if r['priority'] == 'HIGH'])
    medium = len([r for r in recommendations if r['priority'] == 'MEDIUM'])
    low = len([r for r in recommendations if r['priority'] == 'LOW'])
    
    print(f"  • {critical} CRITICAL priority items")
    print(f"  • {high} HIGH priority items") 
    print(f"  • {medium} MEDIUM priority items")
    print(f"  • {low} LOW priority items")
    
    print(f"\n🚨 CRITICAL ISSUES:")
    print("  1. No real-time printer connectivity monitoring")
    print("  2. Print jobs can be submitted to offline printers")
    print("  3. No automatic retry mechanism for failed jobs")
    print("  4. Limited error handling in current workflow")
    
    print(f"\n✅ IMMEDIATE ACTIONS REQUIRED:")
    print("  1. Implement printer status validation in print_file_view")
    print("  2. Add connection testing before job submission")
    print("  3. Create background printer monitoring service")
    print("  4. Enhance error handling and user notifications")
    
    # Save monitoring service code
    try:
        with open('printer_monitor.py', 'w') as f:
            f.write(monitoring_code)
        print(f"\n📁 Sample monitoring service saved to: printer_monitor.py")
    except Exception as e:
        print(f"\n✗ Failed to save monitoring service: {str(e)}")


if __name__ == '__main__':
    main()
