"""
Print job models for PrintSmart backend.
Handles print job management, queuing, and tracking.
"""

import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Printer(models.Model):
    """
    Printer management model.
    """
    
    PRINTER_TYPES = [
        ('laser', 'Laser'),
        ('inkjet', 'Inkjet'),
        ('thermal', 'Thermal'),
        ('dot_matrix', 'Dot Matrix'),
    ]
    
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('busy', 'Busy'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    printer_type = models.CharField(max_length=20, choices=PRINTER_TYPES)
    
    # Network details
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    port = models.IntegerField(blank=True, null=True)
    network_path = models.CharField(max_length=255, blank=True)  # For network printers
    
    # Capabilities
    supports_color = models.BooleanField(default=False)
    supports_duplex = models.BooleanField(default=False)
    max_paper_size = models.CharField(max_length=10, default='A4')
    
    # Status and monitoring
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Usage statistics
    total_pages_printed = models.IntegerField(default=0)
    last_maintenance = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'printers'
        verbose_name = 'Printer'
        verbose_name_plural = 'Printers'
        
    def __str__(self):
        return f"{self.name} ({self.status})"
        
    def update_status(self, status):
        """Update printer status"""
        self.status = status
        self.save()
        
    def add_printed_pages(self, pages):
        """Add to total pages printed"""
        self.total_pages_printed += pages
        self.save()
    
    def test_connection(self):
        """Test printer connectivity"""
        import socket
        import subprocess
        
        if not self.ip_address:
            return False, "No IP address configured"
        
        try:
            # Test ping first
            result = subprocess.run(
                ['ping', '-n', '1', '-w', '3000', self.ip_address],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return False, f"Ping to {self.ip_address} failed"
            
            # Test port if specified
            if self.port:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((self.ip_address, self.port))
                sock.close()
                
                if result != 0:
                    return False, f"Port {self.port} is not accessible"
            
            return True, "Connection successful"
            
        except subprocess.TimeoutExpired:
            return False, "Connection timeout"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def check_and_update_status(self):
        """Check connection and update status automatically"""
        is_connected, message = self.test_connection()
        
        if is_connected:
            if self.status in ['offline', 'error']:
                self.update_status('online')
                return True, "Printer is back online"
        else:
            if self.status == 'online':
                self.update_status('offline')
                return False, f"Printer went offline: {message}"
        
        return is_connected, message


class PrintJob(models.Model):
    """
    Main print job model.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('printing', 'Printing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('paused', 'Paused'),
    ]
    
    COLOR_MODES = [
        ('color', 'Color'),
        ('bw', 'Black & White'),
        ('grayscale', 'Grayscale'),
    ]
    
    PAPER_SIZES = [
        ('A4', 'A4'),
        ('A3', 'A3'),
        ('Letter', 'Letter'),
        ('Legal', 'Legal'),
        ('Custom', 'Custom'),
    ]
    
    PRINT_QUALITY = [
        ('draft', 'Draft'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('best', 'Best'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='print_jobs')
    file = models.ForeignKey('files.File', on_delete=models.CASCADE, related_name='print_jobs')
    printer = models.ForeignKey(Printer, on_delete=models.SET_NULL, null=True, related_name='print_jobs')
    
    # Print settings
    copies = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(1000)])
    pages = models.CharField(max_length=100, default='all')  # e.g., "1-5,8,10-12" or "all"
    color_mode = models.CharField(max_length=10, choices=COLOR_MODES, default='bw')
    paper_size = models.CharField(max_length=10, choices=PAPER_SIZES, default='A4')
    print_quality = models.CharField(max_length=10, choices=PRINT_QUALITY, default='normal')
    
    # Advanced settings
    duplex = models.BooleanField(default=False)
    collate = models.BooleanField(default=True)
    orientation = models.CharField(
        max_length=10,
        choices=[('portrait', 'Portrait'), ('landscape', 'Landscape')],
        default='portrait'
    )
    
    # Job details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    # Cost and billing
    cost_per_page = models.DecimalField(max_digits=6, decimal_places=2, default=0.10)
    total_pages = models.IntegerField(default=1)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tokens_required = models.IntegerField(default=1)
    tokens_deducted = models.BooleanField(default=False)
    
    # Progress tracking
    pages_printed = models.IntegerField(default=0)
    progress_percentage = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    estimated_completion = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    job_settings = models.JSONField(default=dict, blank=True)
    print_metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'print_jobs'
        verbose_name = 'Print Job'
        verbose_name_plural = 'Print Jobs'
        ordering = ['-submitted_at']
        
    def __str__(self):
        return f"Print Job #{self.id} - {self.file.original_filename} ({self.status})"
        
    def calculate_total_cost(self):
        """Calculate total cost based on pages and settings"""
        base_cost = self.cost_per_page * self.total_pages * self.copies
        
        # Color multiplier
        if self.color_mode == 'color':
            base_cost *= 2
        elif self.color_mode == 'grayscale':
            base_cost *= 1.5
            
        # Quality multiplier
        quality_multipliers = {
            'draft': 0.8,
            'normal': 1.0,
            'high': 1.5,
            'best': 2.0
        }
        base_cost *= quality_multipliers.get(self.print_quality, 1.0)
        
        self.total_cost = round(base_cost, 2)
        self.tokens_required = max(1, int(self.total_cost))
        return self.total_cost
        
    def can_user_afford(self):
        """Check if user has sufficient tokens"""
        return self.user.tokens >= self.tokens_required
        
    def deduct_tokens(self):
        """Deduct tokens from user account"""
        if self.can_user_afford() and not self.tokens_deducted:
            success = self.user.deduct_tokens(self.tokens_required)
            if success:
                self.tokens_deducted = True
                self.save()
            return success
        return False
        
    def update_progress(self, pages_printed=None, percentage=None):
        """Update print job progress"""
        if pages_printed is not None:
            self.pages_printed = pages_printed
            self.progress_percentage = int((pages_printed / (self.total_pages * self.copies)) * 100)
        elif percentage is not None:
            self.progress_percentage = percentage
            
        self.save()
    
    def mark_failed(self, error_message, should_retry=True):
        """Mark job as failed and handle retry logic"""
        from django.utils import timezone
        
        self.error_message = error_message
        self.status = 'failed'
        
        if should_retry and self.retry_count < self.max_retries:
            self.retry_count += 1
            self.status = 'pending'  # Queue for retry
            self.save()
            
            # Create notification for retry
            try:
                from core.models import Notification
                Notification.objects.create(
                    user=self.user,
                    title="Print Job Retry",
                    message=f"Print job for {self.file.original_filename} failed but will be retried (attempt {self.retry_count}/{self.max_retries})",
                    notification_type='print_job'
                )
            except ImportError:
                pass  # Notification system not available
            
            return True  # Will retry
        else:
            # Max retries exceeded or retry disabled
            self.save()
            
            # Refund user if payment was deducted
            if hasattr(self, 'total_cost') and self.total_cost:
                self.user.wallet_balance += self.total_cost
                self.user.save()
                
                # Create refund payment record
                try:
                    from payments.models import Payment
                    import time
                    reference_number = f"REFUND_{int(time.time())}_{self.user.id}"
                    Payment.objects.create(
                        user=self.user,
                        amount=self.total_cost,
                        payment_method='refund',
                        description=f'Refund for failed print job: {self.file.original_filename}',
                        status='completed',
                        reference_number=reference_number
                    )
                except ImportError:
                    pass
            
            # Create failure notification
            try:
                from core.models import Notification
                Notification.objects.create(
                    user=self.user,
                    title="Print Job Failed",
                    message=f"Print job for {self.file.original_filename} has permanently failed. You have been refunded.",
                    notification_type='print_job'
                )
            except ImportError:
                pass
            
            return False  # No more retries
    
    def can_retry(self):
        """Check if job can be retried"""
        return (self.status == 'failed' and 
                self.retry_count < self.max_retries and 
                self.printer and 
                self.printer.status == 'online')
    
    def retry_job(self):
        """Retry a failed job"""
        if not self.can_retry():
            return False, "Job cannot be retried"
        
        # Check printer connection before retry
        if hasattr(self.printer, 'test_connection'):
            is_connected, message = self.printer.test_connection()
            if not is_connected:
                return False, f"Printer still offline: {message}"
        
        # Reset job status for retry
        self.status = 'pending'
        self.error_message = ''
        self.retry_count += 1
        self.save()
        
        return True, f"Job queued for retry (attempt {self.retry_count})"


class PrintJobStatusHistory(models.Model):
    """
    Track status changes for print jobs.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    print_job = models.ForeignKey(PrintJob, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='status_changes'
    )
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'print_job_status_history'
        verbose_name = 'Print Job Status History'
        verbose_name_plural = 'Print Job Status Histories'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"Job {self.print_job.id}: {self.previous_status} → {self.new_status}"


class PrintQueue(models.Model):
    """
    Print queue management for printers.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE, related_name='queue')
    print_job = models.ForeignKey(PrintJob, on_delete=models.CASCADE, related_name='queue_entries')
    
    # Queue management
    position = models.IntegerField()
    estimated_start_time = models.DateTimeField(blank=True, null=True)
    estimated_duration = models.DurationField(blank=True, null=True)
    
    # Queue metadata
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'print_queue'
        verbose_name = 'Print Queue Entry'
        verbose_name_plural = 'Print Queue Entries'
        ordering = ['position']
        unique_together = ['printer', 'position']
        
    def __str__(self):
        return f"Queue #{self.position}: {self.print_job.id} on {self.printer.name}"


class PrintJobLog(models.Model):
    """
    Detailed logging for print job events.
    """
    
    LOG_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    print_job = models.ForeignKey(PrintJob, on_delete=models.CASCADE, related_name='logs')
    level = models.CharField(max_length=10, choices=LOG_LEVELS, default='INFO')
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'print_job_logs'
        verbose_name = 'Print Job Log'
        verbose_name_plural = 'Print Job Logs'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"[{self.level}] Job {self.print_job.id}: {self.message[:50]}"
