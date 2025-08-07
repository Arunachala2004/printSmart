"""
Django management command for print job timeout management
Usage: python manage.py manage_job_timeouts
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from print_jobs.models import PrintJob
from payments.models import Payment
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage print job timeouts and cleanup stale jobs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pending-timeout',
            type=int,
            default=30,
            help='Minutes after which pending jobs expire (default: 30)'
        )
        parser.add_argument(
            '--processing-timeout',
            type=int,
            default=60,
            help='Minutes after which processing jobs are considered stuck (default: 60)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--test-mode',
            action='store_true',
            help='Test mode - update job status but do not process refunds'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )

    def handle(self, *args, **options):
        self.verbosity = options.get('verbosity', 1)
        self.verbose = options.get('verbose', False)
        self.dry_run = options.get('dry_run', False)
        self.test_mode = options.get('test_mode', False)
        pending_timeout_minutes = options.get('pending_timeout', 30)
        processing_timeout_minutes = options.get('processing_timeout', 60)

        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        elif self.test_mode:
            self.stdout.write(
                self.style.WARNING('TEST MODE - Job status will be updated but no refunds processed')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Job Timeout Management Service'
                f'\n  Pending timeout: {pending_timeout_minutes} minutes'
                f'\n  Processing timeout: {processing_timeout_minutes} minutes'
                f'\n  Mode: {"DRY RUN" if self.dry_run else "TEST MODE" if self.test_mode else "PRODUCTION"}'
            )
        )

        # Calculate cutoff times
        now = timezone.now()
        pending_cutoff = now - timedelta(minutes=pending_timeout_minutes)
        processing_cutoff = now - timedelta(minutes=processing_timeout_minutes)

        # Handle expired pending jobs
        expired_pending = self.handle_expired_pending_jobs(pending_cutoff)
        
        # Handle stuck processing jobs
        stuck_processing = self.handle_stuck_processing_jobs(processing_cutoff)
        
        # Handle abandoned jobs (very old)
        abandoned_jobs = self.handle_abandoned_jobs(now - timedelta(days=7))

        # Summary
        total_processed = expired_pending + stuck_processing + abandoned_jobs
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nTimeout Management Summary:'
                f'\n  Expired pending jobs: {expired_pending}'
                f'\n  Stuck processing jobs: {stuck_processing}'
                f'\n  Abandoned jobs cleaned: {abandoned_jobs}'
                f'\n  Total jobs processed: {total_processed}'
            )
        )

        if total_processed > 0 and not self.dry_run:
            mode_info = "TEST MODE" if self.test_mode else "PRODUCTION MODE"
            refund_info = " (no refunds in test mode)" if self.test_mode else ""
            logger.info(f'Job timeout management processed {total_processed} jobs in {mode_info}{refund_info}')

    def handle_expired_pending_jobs(self, cutoff_time):
        """Handle jobs that have been pending too long"""
        expired_jobs = PrintJob.objects.filter(
            status='pending',
            submitted_at__lt=cutoff_time
        )

        count = expired_jobs.count()
        if count == 0:
            if self.verbose:
                self.stdout.write('No expired pending jobs found')
            return 0

        self.stdout.write(f'Found {count} expired pending jobs')

        for job in expired_jobs:
            age_minutes = int((timezone.now() - job.submitted_at).total_seconds() / 60)
            
            if self.verbose:
                self.stdout.write(
                    f'  Job {job.id}: {job.file.original_filename} '
                    f'(pending for {age_minutes} minutes)'
                )

                if not self.dry_run:
                    # Check if job can be retried due to printer issues
                    if job.printer and job.printer.status in ['offline', 'error', 'maintenance']:
                        # Printer issue - mark for retry
                        success = job.mark_failed(
                            f'Job expired due to printer {job.printer.name} being {job.printer.status}',
                            should_retry=True
                        )
                        if success:
                            if self.verbose:
                                self.stdout.write(f'    → Queued for retry (printer issue)')
                        else:
                            if self.verbose:
                                self.stdout.write(f'    → Failed permanently (max retries exceeded)')
                    else:
                        # No printer issue - expire the job
                        self.expire_job(job, 'Job expired due to timeout')

        return count

    def handle_stuck_processing_jobs(self, cutoff_time):
        """Handle jobs stuck in processing state"""
        stuck_jobs = PrintJob.objects.filter(
            status__in=['processing', 'printing'],
            started_at__lt=cutoff_time
        ).exclude(started_at__isnull=True)

        count = stuck_jobs.count()
        if count == 0:
            if self.verbose:
                self.stdout.write('No stuck processing jobs found')
            return 0

        self.stdout.write(f'Found {count} stuck processing jobs')

        for job in stuck_jobs:
            if job.started_at:
                age_minutes = int((timezone.now() - job.started_at).total_seconds() / 60)
                
                if self.verbose:
                    self.stdout.write(
                        f'  Job {job.id}: {job.file.original_filename} '
                        f'(processing for {age_minutes} minutes)'
                    )

                if not self.dry_run:
                    # Mark as failed and attempt retry
                    success = job.mark_failed(
                        f'Job stuck in {job.status} state for {age_minutes} minutes',
                        should_retry=True
                    )
                    
                    if success and self.verbose:
                        self.stdout.write(f'    → Reset for retry')
                    elif self.verbose:
                        self.stdout.write(f'    → Failed permanently')

        return count

    def handle_abandoned_jobs(self, cutoff_time):
        """Handle very old jobs that should be cleaned up"""
        abandoned_jobs = PrintJob.objects.filter(
            status__in=['pending', 'failed'],
            submitted_at__lt=cutoff_time
        )

        count = abandoned_jobs.count()
        if count == 0:
            if self.verbose:
                self.stdout.write('No abandoned jobs found')
            return 0

        self.stdout.write(f'Found {count} abandoned jobs (>7 days old)')

        for job in abandoned_jobs:
            age_days = int((timezone.now() - job.submitted_at).total_seconds() / 86400)
            
            if self.verbose:
                self.stdout.write(
                    f'  Job {job.id}: {job.file.original_filename} '
                    f'({age_days} days old, status: {job.status})'
                )

            if not self.dry_run:
                if job.status == 'pending':
                    # Expire pending jobs
                    self.expire_job(job, f'Job abandoned after {age_days} days')
                elif job.status == 'failed':
                    # Just log failed jobs for cleanup consideration
                    if self.verbose:
                        self.stdout.write(f'    → Failed job kept for records')

        return count

    def expire_job(self, job, reason):
        """Expire a job and handle refunds"""
        try:
            # In test mode, skip refund processing
            if self.test_mode:
                if self.verbose:
                    self.stdout.write(f'    → TEST MODE: Skipping refund of ${job.total_cost} for {job.user.email}')
            else:
                # Refund user if payment was made
                if hasattr(job, 'total_cost') and job.total_cost and job.total_cost > 0:
                    user = job.user
                    user.wallet_balance += job.total_cost
                    user.save()

                    # Create refund payment record
                    import time
                    reference_number = f"TIMEOUT_REFUND_{int(time.time())}_{user.id}"
                    Payment.objects.create(
                        user=user,
                        amount=job.total_cost,
                        payment_method='refund',
                        description=f'Timeout refund: {job.file.original_filename}',
                        status='completed',
                        reference_number=reference_number
                    )

                    if self.verbose:
                        self.stdout.write(f'    → ${job.total_cost} refunded to user')

            # Update job status (always do this, even in test mode)
            job.status = 'cancelled'
            job.error_message = reason + (" (TEST MODE - no refund processed)" if self.test_mode else "")
            job.completed_at = timezone.now()
            job.save()

            # Create notification if system available (skip in test mode)
            if not self.test_mode:
                try:
                    from core.models import Notification
                    Notification.objects.create(
                        user=job.user,
                        title="Print Job Expired",
                        message=f'Print job for "{job.file.original_filename}" expired due to timeout. You have been refunded.',
                        notification_type='print_job'
                    )
                except ImportError:
                    pass  # Notification system not available

            status_msg = f'Job {job.id} expired: {reason}'
            if self.test_mode:
                status_msg += ' (TEST MODE - no refund)'
            logger.info(status_msg)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error expiring job {job.id}: {str(e)}')
            )
            logger.error(f'Error expiring job {job.id}: {str(e)}')
