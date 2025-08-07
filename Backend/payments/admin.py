from django.contrib import admin
from .models import Payment, TokenPackage, RazorpayOrder

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['user__username', 'user__email', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

@admin.register(TokenPackage)
class TokenPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'token_count', 'bonus_tokens', 'total_tokens', 'price', 'is_active', 'is_featured']
    list_filter = ['is_active', 'is_featured']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['sort_order', 'price']
    
    def total_tokens(self, obj):
        return obj.total_tokens
    total_tokens.short_description = 'Total Tokens'

@admin.register(RazorpayOrder)
class RazorpayOrderAdmin(admin.ModelAdmin):
    list_display = ['razorpay_order_id', 'user', 'amount', 'order_type', 'status', 'created_at']
    list_filter = ['order_type', 'status', 'created_at']
    search_fields = ['user__username', 'razorpay_order_id', 'razorpay_payment_id']
    readonly_fields = ['created_at', 'updated_at', 'paid_at']
    ordering = ['-created_at']
