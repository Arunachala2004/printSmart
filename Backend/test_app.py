#!/usr/bin/env python
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')

try:
    import django
    django.setup()
    print("✓ Django setup successful")
    
    # Test database connection
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("SELECT 1")
    print("✓ Database connection successful")
    
    # Test user model
    from users.models import User
    user_count = User.objects.count()
    print(f"✓ User model working - {user_count} users in database")
    
    # Test importing views
    from web.views import home
    print("✓ Web views imported successfully")
    
    # Test URL resolution
    from django.urls import reverse
    home_url = reverse('web:home')
    print(f"✓ URL resolution working - home URL: {home_url}")
    
    print("\n🎉 All checks passed! The application should work properly.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
