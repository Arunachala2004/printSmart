#!/usr/bin/env python3
"""
Manual database creation script for PrintSmart
"""
import os
import sys
import django

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')

try:
    # Setup Django
    django.setup()
    print("✅ Django setup successful")
    
    # Import Django modules
    from django.core.management import call_command
    from django.db import connection
    from users.models import User
    
    print("🔧 Creating database and running migrations...")
    
    # Create migrations for all apps
    call_command('makemigrations', verbosity=2)
    print("✅ Migrations created")
    
    # Apply migrations
    call_command('migrate', verbosity=2)
    print("✅ Migrations applied")
    
    # Check if admin user exists
    try:
        admin_user = User.objects.get(username='admin')
        print("✅ Admin user already exists")
    except User.DoesNotExist:
        print("🔧 Creating admin user...")
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin'
        )
        print("✅ Admin user created:")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Email: admin@example.com")
    
    print("\n🔧 Testing URL resolution...")
    from django.urls import reverse
    
    # Test critical URLs
    test_urls = [
        ('web:home', 'Home page'),
        ('web:dashboard', 'Dashboard'),
        ('web:login', 'Login page'),
        ('web:files', 'Files page'),
        ('web:printers', 'Printers page'),
        ('web:wallet', 'Wallet page'),
    ]
    
    for url_name, description in test_urls:
        try:
            url = reverse(url_name)
            print(f"✅ {description}: {url}")
        except Exception as e:
            print(f"❌ {description} ({url_name}): {e}")
    
    print("\n🎉 Database setup completed successfully!")
    print("🚀 You can now run the Django server:")
    print("   python manage.py runserver")
    print("🌐 Then visit: http://127.0.0.1:8000")
    
except Exception as e:
    print(f"❌ Setup failed: {e}")
    import traceback
    traceback.print_exc()
    
    # Try to provide helpful error information
    print("\n🔍 Troubleshooting information:")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print(f"Django settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
