"""
File models for PrintSmart backend.
Handles file uploads, processing, and metadata.
"""

import uuid
import os
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator


def upload_to_temp(instance, filename):
    """Upload files to temporary directory"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', 'temp', filename)


def upload_to_processed(instance, filename):
    """Upload processed files to processed directory"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', 'processed', filename)


def upload_to_thumbnails(instance, filename):
    """Upload thumbnails to thumbnails directory"""
    filename = f"{uuid.uuid4()}.jpg"
    return os.path.join('uploads', 'thumbnails', filename)


class File(models.Model):
    """
    Main file model for uploaded files.
    """
    
    FILE_TYPES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('jpg', 'JPG'),
        ('jpeg', 'JPEG'),
        ('png', 'PNG'),
    ]
    
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('error', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='files')
    
    # File information
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    file_size = models.BigIntegerField()  # Size in bytes
    
    # File paths
    original_file = models.FileField(
        upload_to=upload_to_temp,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'jpg', 'jpeg', 'png'])]
    )
    processed_file = models.FileField(upload_to=upload_to_processed, blank=True, null=True)
    thumbnail = models.ImageField(upload_to=upload_to_thumbnails, blank=True, null=True)
    
    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    is_edited = models.BooleanField(default=False)
    
    # Metadata
    page_count = models.IntegerField(default=1)
    width = models.IntegerField(blank=True, null=True)  # For images
    height = models.IntegerField(blank=True, null=True)  # For images
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'files'
        verbose_name = 'File'
        verbose_name_plural = 'Files'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.original_filename} ({self.user.email})"
        
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)
        
    def get_file_url(self):
        """Get the appropriate file URL based on processing status"""
        if self.processed_file:
            return self.processed_file.url
        return self.original_file.url


class FileEditOperation(models.Model):
    """
    Track edit operations performed on files.
    """
    
    OPERATION_TYPES = [
        ('rotate', 'Rotate'),
        ('delete_page', 'Delete Page'),
        ('crop', 'Crop'),
        ('merge', 'Merge'),
        ('split', 'Split'),
        ('watermark', 'Watermark'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='edit_operations')
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    parameters = models.JSONField(default=dict)  # Store operation parameters
    applied_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'file_edit_operations'
        verbose_name = 'File Edit Operation'
        verbose_name_plural = 'File Edit Operations'
        ordering = ['-applied_at']
        
    def __str__(self):
        return f"{self.operation_type} on {self.file.original_filename}"


class FileShare(models.Model):
    """
    File sharing functionality.
    """
    
    PERMISSION_CHOICES = [
        ('view', 'View Only'),
        ('download', 'Download'),
        ('edit', 'Edit'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='shares')
    shared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_files')
    shared_with = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_files',
        blank=True,
        null=True
    )
    
    # Sharing options
    share_token = models.CharField(max_length=64, unique=True)  # For public sharing
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='view')
    expires_at = models.DateTimeField(blank=True, null=True)
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Analytics
    access_count = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'file_shares'
        verbose_name = 'File Share'
        verbose_name_plural = 'File Shares'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Share: {self.file.original_filename} by {self.shared_by.email}"
        
    def increment_access_count(self):
        """Increment access count"""
        self.access_count += 1
        self.last_accessed = models.DateTimeField(auto_now=True)
        self.save()


class FileProcessingTask(models.Model):
    """
    Track background file processing tasks.
    """
    
    TASK_TYPES = [
        ('thumbnail_generation', 'Thumbnail Generation'),
        ('pdf_optimization', 'PDF Optimization'),
        ('format_conversion', 'Format Conversion'),
        ('compression', 'Compression'),
        ('virus_scan', 'Virus Scan'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='processing_tasks')
    task_type = models.CharField(max_length=30, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Task details
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)
    progress = models.IntegerField(default=0)  # 0-100
    error_message = models.TextField(blank=True)
    result_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'file_processing_tasks'
        verbose_name = 'File Processing Task'
        verbose_name_plural = 'File Processing Tasks'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.task_type} for {self.file.original_filename} - {self.status}"
