"""
Payment models for PrintSmart backend.
Handles payment processing, token management, and billing.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class TokenPackage(models.Model):
    """
    Define token packages available for purchase.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    token_count = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    bonus_tokens = models.IntegerField(default=0)  # Extra tokens for bulk purchases
    
    # Package settings
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    
    # Validity
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'token_packages'
        verbose_name = 'Token Package'
        verbose_name_plural = 'Token Packages'
        ordering = ['sort_order', 'price']
        
    def __str__(self):
        return f"{self.name} - {self.token_count} tokens (₹{self.price})"
        
    @property
    def total_tokens(self):
        """Total tokens including bonus"""
        return self.token_count + self.bonus_tokens
        
    @property
    def price_per_token(self):
        """Price per token"""
        return self.price / self.total_tokens if self.total_tokens > 0 else 0


class Payment(models.Model):
    """
    Payment transaction model.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]
    
    PAYMENT_METHODS = [
        ('razorpay', 'Razorpay'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('wallet', 'Wallet'),
        ('admin_credit', 'Admin Credit'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    token_package = models.ForeignKey(TokenPackage, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='razorpay')
    
    # External payment provider details
    provider_payment_id = models.CharField(max_length=255, blank=True)  # Razorpay payment ID
    provider_order_id = models.CharField(max_length=255, blank=True)   # Razorpay order ID
    provider_signature = models.CharField(max_length=255, blank=True)  # Razorpay signature
    provider_response = models.JSONField(default=dict, blank=True)     # Full provider response
    
    # Token details
    tokens_purchased = models.IntegerField(default=0)
    tokens_credited = models.BooleanField(default=False)
    
    # Transaction metadata
    description = models.TextField(blank=True)
    reference_number = models.CharField(max_length=50, unique=True, blank=True)
    invoice_number = models.CharField(max_length=50, blank=True)
    
    # Billing information
    billing_name = models.CharField(max_length=100, blank=True)
    billing_email = models.EmailField(blank=True)
    billing_phone = models.CharField(max_length=15, blank=True)
    billing_address = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Admin fields
    admin_notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_payments'
    )
    
    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Payment #{self.id} - {self.user.email} - ₹{self.amount} ({self.status})"
        
    def generate_reference_number(self):
        """Generate unique reference number"""
        if not self.reference_number:
            import time
            timestamp = str(int(time.time()))
            self.reference_number = f"PS{timestamp}{str(self.id)[:8]}"
            
    def credit_tokens(self):
        """Credit tokens to user account"""
        if self.status == 'completed' and not self.tokens_credited and self.tokens_purchased > 0:
            self.user.add_tokens(self.tokens_purchased)
            self.tokens_credited = True
            self.save()
            
            # Create token transaction record
            TokenTransaction.objects.create(
                user=self.user,
                transaction_type='credit',
                amount=self.tokens_purchased,
                description=f"Token purchase - Payment #{self.id}",
                payment=self,
                balance_after=self.user.tokens
            )
            return True
        return False


class TokenTransaction(models.Model):
    """
    Track all token transactions for users.
    """
    
    TRANSACTION_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('refund', 'Refund'),
        ('bonus', 'Bonus'),
        ('admin_adjustment', 'Admin Adjustment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='token_transactions')
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.IntegerField()  # Can be negative for debits
    description = models.TextField()
    
    # References
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    print_job = models.ForeignKey('print_jobs.PrintJob', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Balance tracking
    balance_before = models.IntegerField(default=0)
    balance_after = models.IntegerField(default=0)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_token_transactions'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'token_transactions'
        verbose_name = 'Token Transaction'
        verbose_name_plural = 'Token Transactions'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.transaction_type.title()}: {self.amount} tokens for {self.user.email}"


class Invoice(models.Model):
    """
    Invoice generation for payments.
    """
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='invoice')
    
    # Invoice details
    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Billing details
    bill_to_name = models.CharField(max_length=100)
    bill_to_email = models.EmailField()
    bill_to_address = models.TextField()
    
    # Company details
    company_name = models.CharField(max_length=100, default='PrintSmart')
    company_address = models.TextField(blank=True)
    company_tax_id = models.CharField(max_length=50, blank=True)
    
    # Dates
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    paid_date = models.DateField(blank=True, null=True)
    
    # Files
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    
    # Notes
    notes = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.bill_to_email}"
        
    def calculate_total(self):
        """Calculate total amount with tax and discount"""
        self.tax_amount = (self.subtotal * self.tax_rate) / 100
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        return self.total_amount


class Refund(models.Model):
    """
    Handle refund transactions.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    REFUND_TYPES = [
        ('full', 'Full Refund'),
        ('partial', 'Partial Refund'),
        ('token_adjustment', 'Token Adjustment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='refunds')
    
    # Refund details
    refund_type = models.CharField(max_length=20, choices=REFUND_TYPES, default='full')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    tokens_to_deduct = models.IntegerField(default=0)
    reason = models.TextField()
    
    # Provider details
    provider_refund_id = models.CharField(max_length=255, blank=True)
    provider_response = models.JSONField(default=dict, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Admin details
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_refunds'
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_refunds'
    )
    admin_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'refunds'
        verbose_name = 'Refund'
        verbose_name_plural = 'Refunds'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Refund #{self.id} - ₹{self.amount} for Payment #{self.payment.id}"
        
    def process_refund(self):
        """Process the refund and adjust user tokens"""
        if self.status == 'completed' and self.tokens_to_deduct > 0:
            # Deduct tokens from user
            success = self.user.deduct_tokens(self.tokens_to_deduct)
            if success:
                # Create token transaction record
                TokenTransaction.objects.create(
                    user=self.user,
                    transaction_type='debit',
                    amount=-self.tokens_to_deduct,
                    description=f"Refund adjustment - Refund #{self.id}",
                    balance_after=self.user.tokens,
                    created_by=self.processed_by
                )
            return success
        return True


class PaymentWebhook(models.Model):
    """
    Store webhook data from payment providers.
    """
    
    PROVIDER_CHOICES = [
        ('razorpay', 'Razorpay'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    event_type = models.CharField(max_length=50)
    
    # Webhook data
    webhook_id = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict)
    headers = models.JSONField(default=dict)
    signature = models.TextField(blank=True)
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)
    
    # Related payment
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'payment_webhooks'
        verbose_name = 'Payment Webhook'
        verbose_name_plural = 'Payment Webhooks'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.provider} - {self.event_type} - {self.created_at}"
