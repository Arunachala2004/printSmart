"""
Core models for PrintSmart backend.
Shared utilities and base models.
"""

import uuid
from django.db import models
from django.conf import settings


class BaseModel(models.Model):
    """
    Abstract base model with common fields.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class SystemSettings(models.Model):
    """
    System-wide configuration settings.
    """
    
    SETTING_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    ]
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    setting_type = models.CharField(max_length=10, choices=SETTING_TYPES, default='string')
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)  # Can be accessed by frontend
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
        
    def __str__(self):
        return f"{self.key}: {self.value}"
        
    def get_value(self):
        """Get typed value based on setting_type"""
        if self.setting_type == 'integer':
            return int(self.value)
        elif self.setting_type == 'float':
            return float(self.value)
        elif self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == 'json':
            import json
            return json.loads(self.value)
        return self.value


class Notification(models.Model):
    """
    User notifications system.
    """
    
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('print_job', 'Print Job'),
        ('payment', 'Payment'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification content
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    
    # Status
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    # Related objects
    related_object_type = models.CharField(max_length=50, blank=True)  # Model name
    related_object_id = models.CharField(max_length=255, blank=True)   # Object ID
    
    # Action
    action_url = models.URLField(blank=True)
    action_text = models.CharField(max_length=50, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} for {self.user.email}"
        
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = models.DateTimeField(auto_now=True)
            self.save()


class AuditLog(models.Model):
    """
    System audit logging.
    """
    
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('permission_change', 'Permission Change'),
        ('system_config', 'System Configuration'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    
    # Action details
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    resource_type = models.CharField(max_length=50)  # Model name
    resource_id = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    
    # Request details
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    
    # Changes
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    # Metadata
    session_key = models.CharField(max_length=40, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.action} {self.resource_type} by {self.user.email if self.user else 'System'}"


class EmailTemplate(models.Model):
    """
    Email templates for system notifications.
    """
    
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Email'),
        ('password_reset', 'Password Reset'),
        ('email_verification', 'Email Verification'),
        ('print_job_completed', 'Print Job Completed'),
        ('payment_successful', 'Payment Successful'),
        ('payment_failed', 'Payment Failed'),
        ('token_low', 'Low Token Balance'),
        ('system_maintenance', 'System Maintenance'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES, unique=True)
    
    # Email content
    subject = models.CharField(max_length=200)
    html_content = models.TextField()
    text_content = models.TextField()
    
    # Template variables help
    available_variables = models.JSONField(default=list, blank=True)
    variable_descriptions = models.JSONField(default=dict, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'email_templates'
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
        
    def __str__(self):
        return f"{self.name} ({self.template_type})"
        
    def render(self, context=None):
        """Render template with context variables"""
        if context is None:
            context = {}
            
        from django.template import Template, Context
        
        # Render subject
        subject_template = Template(self.subject)
        rendered_subject = subject_template.render(Context(context))
        
        # Render HTML content
        html_template = Template(self.html_content)
        rendered_html = html_template.render(Context(context))
        
        # Render text content
        text_template = Template(self.text_content)
        rendered_text = text_template.render(Context(context))
        
        return {
            'subject': rendered_subject,
            'html_content': rendered_html,
            'text_content': rendered_text
        }
