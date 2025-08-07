#!/usr/bin/env python
"""
PrintSmart Operational Error Fix Script
This script fixes common operational errors that occur when running Django.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')

def check_database():
    """Check if database exists and has required tables"""
    db_path = 'db.sqlite3'
    
    if not os.path.exists(db_path):
        print("❌ Database file missing")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users_user';")
        if not cursor.fetchone():
            print("❌ Users table missing")
            return False
            
        print("✓ Database and tables exist")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def fix_migrations():
    """Run migrations to fix database issues"""
    print("🔧 Running migrations...")
    
    # Delete existing database
    if os.path.exists('db.sqlite3'):
        os.remove('db.sqlite3')
        print("  - Deleted old database")
    
    # Remove migration files (except __init__.py)
    for app in ['users', 'files', 'print_jobs', 'payments', 'core']:
        migrations_dir = Path(app) / 'migrations'
        if migrations_dir.exists():
            for file in migrations_dir.glob('*.py'):
                if file.name != '__init__.py':
                    file.unlink()
                    print(f"  - Removed {file}")
    
    # Run Django commands
    import django
    django.setup()
    
    from django.core.management import execute_from_command_line
    
    # Make fresh migrations
    execute_from_command_line(['manage.py', 'makemigrations'])
    print("  - Created new migrations")
    
    # Apply migrations
    execute_from_command_line(['manage.py', 'migrate'])
    print("  - Applied migrations")

def create_superuser():
    """Create admin user"""
    import django
    django.setup()
    
    from users.models import User
    
    try:
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@printsmart.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                wallet_balance=1000.00
            )
            print("✓ Created admin user (admin/admin123)")
        else:
            print("✓ Admin user already exists")
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")

def main():
    print("🚀 PrintSmart Operational Error Fix")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Not in Django project directory")
        return
    
    # Check database
    if not check_database():
        print("🔧 Fixing database issues...")
        fix_migrations()
    
    # Create superuser
    create_superuser()
    
    print("\n✅ Fix completed!")
    print("You can now run: python manage.py runserver")
    print("Admin login: admin / admin123")

if __name__ == '__main__':
    main()
