
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
    