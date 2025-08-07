#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')

try:
    django.setup()
    print("✓ Django setup successful")
    
    # Test imports
    from web.views import home
    print("✓ Views import successful")
    
    from web.urls import urlpatterns
    print("✓ URLs import successful")
    
    # Test database connection
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("SELECT 1")
    print("✓ Database connection successful")
    
    print("\n🎉 All basic checks passed! Starting server...")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
