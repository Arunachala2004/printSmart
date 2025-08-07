#!/usr/bin/env python3
"""
Django management script to fix database issues
"""
import os
import sys
import django

# Add the current directory to Python path
sys.path.insert(0, '.')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')
django.setup()

from django.core.management import execute_from_command_line

def run_management_command(command):
    """Run a Django management command"""
    try:
        print(f"Running: {' '.join(command)}")
        execute_from_command_line(command)
        print(f"✅ Command completed successfully: {' '.join(command)}")
        return True
    except Exception as e:
        print(f"❌ Command failed: {' '.join(command)}")
        print(f"Error: {e}")
        return False

def setup_database():
    """Setup database with migrations and superuser"""
    print("🔧 Setting up database...")
    
    # Run migrations
    if run_management_command(['manage.py', 'migrate']):
        print("✅ Database migrations completed")
    else:
        print("❌ Database migrations failed")
        return False
    
    # Check if admin user exists
    from users.models import User
    
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
        print("✅ Admin user created successfully")
        print("Username: admin")
        print("Password: admin123")
    
    return True

def check_urls():
    """Check if URL patterns work"""
    try:
        from django.urls import reverse
        print("\n🔧 Testing URL patterns...")
        
        urls_to_test = [
            'web:home',
            'web:dashboard',
            'web:login',
            'web:register',
            'web:files',
            'web:printers',
            'web:print_jobs',
            'web:wallet',
        ]
        
        for url_name in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"✅ {url_name}: {url}")
            except Exception as e:
                print(f"❌ {url_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ URL testing failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 PrintSmart Database Setup")
    print("=" * 40)
    
    if setup_database():
        check_urls()
        print("\n🎉 Setup completed!")
        print("You can now run: python manage.py runserver")
    else:
        print("\n❌ Setup failed!")
