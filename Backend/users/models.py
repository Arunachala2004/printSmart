"""
User models for PrintSmart backend.
Includes custom user model and related functionality.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator


class User(AbstractUser):
    """
    Custom User model with additional fields for PrintSmart functionality.
    """
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    tokens = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Override username to use email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
    def __str__(self):
        return f"{self.email} ({self.role})"
        
    @property
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
        
    def add_tokens(self, amount):
        """Add tokens to user account"""
        self.tokens += amount
        self.save()
        
    def deduct_tokens(self, amount):
        """Deduct tokens from user account if sufficient balance"""
        if self.tokens >= amount:
            self.tokens -= amount
            self.save()
            return True
        return False


class UserProfile(models.Model):
    """
    Extended user profile with additional information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    company = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=50, blank=True)
    
    # Preferences
    default_copies = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    default_color_mode = models.CharField(
        max_length=10,
        choices=[('color', 'Color'), ('bw', 'Black & White')],
        default='bw'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        
    def __str__(self):
        return f"Profile of {self.user.email}"


class UserActivity(models.Model):
    """
    Track user activities for audit and analytics.
    """
    
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('file_upload', 'File Upload'),
        ('print_job', 'Print Job'),
        ('payment', 'Payment'),
        ('token_purchase', 'Token Purchase'),
        ('profile_update', 'Profile Update'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} at {self.timestamp}"
