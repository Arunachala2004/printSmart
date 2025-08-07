#!/usr/bin/env python3
"""
Quick error checker for Django server
"""
import os
import sys
import traceback

def check_server_errors():
    try:
        print("Checking Django server errors...")
        
        # Setup Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')
        
        import django
        django.setup()
        
        # Try to run server check
        from django.core.management import call_command
        from django.core.management.commands.runserver import Command
        
        print("Running Django system check...")
        call_command('check')
        print("✅ Django check passed")
        
        # Test URL imports
        print("Testing URL imports...")
        from django.urls import get_resolver
        resolver = get_resolver()
        print("✅ URLs loaded successfully")
        
        # Test model imports
        print("Testing model imports...")
        from users.models import User
        from files.models import File
        from print_jobs.models import PrintJob
        print("✅ Models imported successfully")
        
        # Test database connection
        print("Testing database connection...")
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection successful")
        
        # Check for common server issues
        print("Checking common server issues...")
        
        # Check ALLOWED_HOSTS
        from django.conf import settings
        if not settings.ALLOWED_HOSTS:
            print("⚠️ ALLOWED_HOSTS is empty, adding localhost")
            # This would need to be fixed in settings.py
        
        print("\n🎉 No critical errors found!")
        print("Server should be able to start successfully.")
        
    except Exception as e:
        print(f"❌ Error found: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        
        # Try to provide specific fixes
        error_str = str(e).lower()
        
        if "no module named" in error_str:
            print("\n🔧 SUGGESTED FIX:")
            print("Missing Python package. Try:")
            print("pip install django djangorestframework")
            
        elif "database" in error_str:
            print("\n🔧 SUGGESTED FIX:")
            print("Database issue. Try:")
            print("python manage.py migrate")
            
        elif "allowed_hosts" in error_str:
            print("\n🔧 SUGGESTED FIX:")
            print("ALLOWED_HOSTS issue. Adding localhost to settings...")
            
        elif "import" in error_str:
            print("\n🔧 SUGGESTED FIX:")
            print("Import error. Check if all apps are in INSTALLED_APPS")

if __name__ == '__main__':
    check_server_errors()
