#!/usr/bin/env python3
"""
PrintSmart Error Diagnostic Script
This script will help identify and fix common issues with the Django application.
"""

import os
import sys
import traceback

def check_python_environment():
    """Check if Python and required packages are available"""
    print("=" * 60)
    print("🐍 PYTHON ENVIRONMENT CHECK")
    print("=" * 60)
    
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check required packages
    required_packages = ['django', 'sqlite3']
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            print(f"❌ {package} is NOT available")
    
    return True

def check_django_setup():
    """Check Django configuration and setup"""
    print("\n" + "=" * 60)
    print("🚀 DJANGO SETUP CHECK")
    print("=" * 60)
    
    try:
        # Set up Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')
        
        import django
        print(f"Django version: {django.get_version()}")
        
        django.setup()
        print("✅ Django setup successful")
        
        # Test settings import
        from django.conf import settings
        print(f"✅ Settings loaded: {settings.DATABASES['default']['NAME']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        traceback.print_exc()
        return False

def check_database():
    """Check database connectivity and structure"""
    print("\n" + "=" * 60)
    print("🗄️ DATABASE CHECK")
    print("=" * 60)
    
    try:
        from django.db import connection
        from django.core.management import call_command
        
        # Check if database file exists
        db_path = 'db.sqlite3'
        if os.path.exists(db_path):
            print(f"✅ Database file exists: {db_path}")
            size = os.path.getsize(db_path)
            print(f"   File size: {size} bytes")
        else:
            print(f"❌ Database file missing: {db_path}")
            print("🔧 Creating database...")
            call_command('migrate', verbosity=0)
            print("✅ Database created")
        
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"✅ Database connection successful")
            print(f"   Found {len(tables)} tables")
        
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        traceback.print_exc()
        return False

def check_models():
    """Check if models can be imported and used"""
    print("\n" + "=" * 60)
    print("📦 MODELS CHECK")
    print("=" * 60)
    
    try:
        from users.models import User
        from files.models import File
        from print_jobs.models import PrintJob
        from payments.models import Payment
        
        print("✅ All models imported successfully")
        
        # Check if admin user exists
        try:
            admin_user = User.objects.get(username='admin')
            print("✅ Admin user exists")
        except User.DoesNotExist:
            print("❌ Admin user missing")
            print("🔧 Creating admin user...")
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role='admin'
            )
            print("✅ Admin user created")
        
        return True
        
    except Exception as e:
        print(f"❌ Models check failed: {e}")
        traceback.print_exc()
        return False

def check_urls():
    """Check URL patterns"""
    print("\n" + "=" * 60)
    print("🔗 URL PATTERNS CHECK")
    print("=" * 60)
    
    try:
        from django.urls import reverse
        
        critical_urls = [
            'web:home',
            'web:dashboard', 
            'web:login',
            'web:register',
            'web:files',
            'web:upload_file',
            'web:printers',
            'web:print_jobs',
            'web:wallet',
        ]
        
        for url_name in critical_urls:
            try:
                url = reverse(url_name)
                print(f"✅ {url_name}: {url}")
            except Exception as e:
                print(f"❌ {url_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ URL check failed: {e}")
        traceback.print_exc()
        return False

def run_server_test():
    """Test if server can start"""
    print("\n" + "=" * 60)
    print("🌐 SERVER TEST")
    print("=" * 60)
    
    try:
        from django.core.management import call_command
        from django.test import Client
        
        # Test client
        client = Client()
        response = client.get('/')
        print(f"✅ Server responds to root request: Status {response.status_code}")
        
        if response.status_code == 302:  # Redirect is expected
            print("   (Redirect to login/dashboard is normal)")
        
        return True
        
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic checks"""
    print("🔍 PRINTSMART DIAGNOSTIC TOOL")
    print("This script will check for common issues and try to fix them.")
    print()
    
    # Change to the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run all checks
    checks = [
        check_python_environment,
        check_django_setup,
        check_database,
        check_models,
        check_urls,
        run_server_test,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Check failed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("🎉 All checks passed! Your Django application should be working.")
        print("\n🚀 To start the server, run:")
        print("   python manage.py runserver")
        print("\n🌐 Then visit: http://127.0.0.1:8000")
        print("\n👤 Admin credentials:")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print(f"⚠️ {total - passed} out of {total} checks failed.")
        print("Please review the errors above and fix any issues.")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
