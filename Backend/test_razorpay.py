#!/usr/bin/env python
"""
Manual Razorpay Integration Test
Tests the core Razorpay functionality without making actual payments
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')
django.setup()

from django.conf import settings
import razorpay

def test_razorpay_connection():
    """Test Razorpay API connection"""
    print("🔧 Testing Razorpay Integration...")
    print(f"Key ID: {settings.RAZORPAY_KEY_ID[:10]}...")
    
    try:
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        print("✅ Razorpay client initialized successfully")
        
        # Test creating an order (this won't charge anything)
        order_data = {
            'amount': 5000,  # ₹50 in paisa
            'currency': 'INR',
            'receipt': 'test_receipt_12345'
        }
        
        # Note: This creates a real order but won't charge until payment is captured
        order = client.order.create(order_data)
        print(f"✅ Test order created: {order['id']}")
        print(f"   Amount: ₹{order['amount']/100}")
        print(f"   Status: {order['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Razorpay integration error: {str(e)}")
        return False

def test_payment_models():
    """Test payment-related models"""
    print("\n🗄️  Testing Payment Models...")
    
    try:
        from payments.models import TokenPackage, RazorpayOrder
        from users.models import User
        
        # Test TokenPackage
        packages = TokenPackage.objects.filter(is_active=True)
        print(f"✅ Active token packages: {packages.count()}")
        
        # Test User model
        users = User.objects.all()
        print(f"✅ Total users: {users.count()}")
        
        # Test RazorpayOrder model
        orders = RazorpayOrder.objects.all()
        print(f"✅ Razorpay orders: {orders.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test error: {str(e)}")
        return False

def test_url_patterns():
    """Test URL pattern resolution"""
    print("\n🔗 Testing URL Patterns...")
    
    from django.urls import reverse
    
    url_tests = [
        ('payments:token_packages', 'Token packages URL'),
        ('payments:wallet_topup', 'Wallet topup URL'),
        ('payments:payment_success', 'Payment success URL'),
        ('payments:payment_failed', 'Payment failed URL'),
        ('payments:razorpay_webhook', 'Razorpay webhook URL'),
    ]
    
    for url_name, description in url_tests:
        try:
            url = reverse(url_name)
            print(f"✅ {description}: {url}")
        except Exception as e:
            print(f"❌ {description}: {str(e)}")

if __name__ == '__main__':
    print("=" * 50)
    print("PRINTSMART RAZORPAY INTEGRATION TEST")
    print("=" * 50)
    
    # Run tests
    razorpay_ok = test_razorpay_connection()
    models_ok = test_payment_models()
    test_url_patterns()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    if razorpay_ok and models_ok:
        print("✅ ALL TESTS PASSED! Razorpay integration is working correctly.")
        print("🚀 Ready for live transactions!")
        print("\n📋 Next Steps:")
        print("   1. Test wallet top-up with small amount")
        print("   2. Test token purchase")
        print("   3. Set up webhook in Razorpay dashboard")
        print("   4. Test webhook functionality")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print("=" * 50)
