"""
Django management command to monitor printer connections
Usage: python manage.py monitor_printers
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from print_jobs.models import Printer, PrintJob
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Monitor printer connections and update status automatically'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Check interval in seconds (default: 60)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run once instead of continuous monitoring'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )

    def handle(self, *args, **options):
        self.verbosity = options.get('verbosity', 1)
        self.verbose = options.get('verbose', False)
        interval = options.get('interval', 60)
        run_once = options.get('once', False)

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting printer monitoring service...'
            )
        )
        
        if run_once:
            self.stdout.write(f'Running single check...')
            self.check_all_printers()
        else:
            self.stdout.write(f'Monitoring interval: {interval} seconds')
            self.stdout.write('Press Ctrl+C to stop monitoring')
            
            try:
                while True:
                    self.check_all_printers()
                    if self.verbose:
                        self.stdout.write(f'Sleeping for {interval} seconds...')
                    time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write(
                    self.style.SUCCESS('\nMonitoring stopped by user')
                )

    def check_all_printers(self):
        """Check all active printers"""
        printers = Printer.objects.filter(is_active=True)
        
        if not printers.exists():
            if self.verbose:
                self.stdout.write('No active printers found')
            return

        self.stdout.write(f'Checking {printers.count()} printers...')
        
        for printer in printers:
            try:
                self.check_printer(printer)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error checking printer {printer.name}: {str(e)}'
                    )
                )
                logger.error(f'Printer check error for {printer.name}: {str(e)}')

    def check_printer(self, printer):
        """Check individual printer and update status"""
        old_status = printer.status
        
        # Test connection
        is_connected, message = printer.check_and_update_status()
        
        if printer.status != old_status:
            self.stdout.write(
                self.style.WARNING(
                    f'Printer {printer.name}: {old_status} -> {printer.status}'
                )
            )
            logger.info(f'Printer {printer.name} status changed: {old_status} -> {printer.status}')
            
            # Handle printer going offline
            if printer.status in ['offline', 'error']:
                self.handle_printer_failure(printer)
            
            # Handle printer coming back online
            elif printer.status == 'online' and old_status in ['offline', 'error']:
                self.handle_printer_recovery(printer)
                
        elif self.verbose:
            self.stdout.write(f'Printer {printer.name}: {printer.status} ({message})')

    def handle_printer_failure(self, printer):
        """Handle print jobs when printer fails"""
        # Find jobs that are pending/processing for this printer
        affected_jobs = PrintJob.objects.filter(
            printer=printer,
            status__in=['pending', 'processing', 'printing']
        )
        
        if affected_jobs.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Found {affected_jobs.count()} jobs affected by printer failure'
                )
            )
            
            for job in affected_jobs:
                error_msg = f'Printer {printer.name} went {printer.status}'
                retry_result = job.mark_failed(error_msg, should_retry=True)
                
                if retry_result:
                    self.stdout.write(f'  Job {job.id}: Queued for retry')
                else:
                    self.stdout.write(f'  Job {job.id}: Failed permanently (refunded)')
                    
                logger.info(f'Job {job.id} affected by printer {printer.name} failure')

    def handle_printer_recovery(self, printer):
        """Handle printer coming back online"""
        # Find failed jobs that can be retried
        retry_jobs = PrintJob.objects.filter(
            printer=printer,
            status='failed'
        )
        
        retryable_jobs = [job for job in retry_jobs if job.can_retry()]
        
        if retryable_jobs:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Printer {printer.name} back online. Found {len(retryable_jobs)} jobs to retry'
                )
            )
            
            for job in retryable_jobs:
                success, message = job.retry_job()
                if success:
                    self.stdout.write(f'  Job {job.id}: {message}')
                    logger.info(f'Job {job.id} queued for retry on recovered printer {printer.name}')
