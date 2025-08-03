#!/usr/bin/env python
"""
PrintSmart Backend Management Script
Provides common operations for managing the Django backend.
"""

import os
import sys
import subprocess
from pathlib import Path

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')

try:
    import django
    django.setup()
except ImportError:
    pass

def run_command(command, description=""):
    """Run a command and display output"""
    print(f"\n🔄 {description}")
    print(f"Command: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(f"✅ Output:\n{result.stdout}")
    if result.stderr:
        print(f"⚠️ Errors:\n{result.stderr}")
    
    return result.returncode == 0

def create_superuser():
    """Create a superuser account"""
    print("\n🔐 Creating Superuser Account")
    print("=" * 50)
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        email = input("Email address: ")
        username = input("Username (optional, will use email): ") or email.split('@')[0]
        
        if User.objects.filter(email=email).exists():
            print(f"❌ User with email {email} already exists!")
            return False
            
        import getpass
        password = getpass.getpass("Password: ")
        password_confirm = getpass.getpass("Confirm password: ")
        
        if password != password_confirm:
            print("❌ Passwords don't match!")
            return False
            
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role='admin'
        )
        
        print(f"✅ Superuser '{email}' created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
        return False

def setup_sample_data():
    """Create sample data for development"""
    print("\n📊 Setting up Sample Data")
    print("=" * 50)
    
    try:
        from django.contrib.auth import get_user_model
        from payments.models import TokenPackage
        from print_jobs.models import Printer
        from core.models import SystemSettings
        
        User = get_user_model()
        
        # Create sample token packages
        packages = [
            {"name": "Starter Pack", "token_count": 10, "price": 10.00, "bonus_tokens": 0},
            {"name": "Value Pack", "token_count": 50, "price": 45.00, "bonus_tokens": 5},
            {"name": "Power Pack", "token_count": 100, "price": 80.00, "bonus_tokens": 20},
            {"name": "Premium Pack", "token_count": 500, "price": 350.00, "bonus_tokens": 150},
        ]
        
        for pkg_data in packages:
            pkg, created = TokenPackage.objects.get_or_create(
                name=pkg_data["name"],
                defaults=pkg_data
            )
            if created:
                print(f"✅ Created token package: {pkg.name}")
        
        # Create sample printer
        printer, created = Printer.objects.get_or_create(
            name="Default Printer",
            defaults={
                "description": "Main office printer",
                "printer_type": "laser",
                "supports_color": True,
                "supports_duplex": True,
                "status": "online",
                "is_default": True
            }
        )
        if created:
            print(f"✅ Created printer: {printer.name}")
        
        # Create system settings
        settings = [
            {"key": "site_name", "value": "PrintSmart", "description": "Site name"},
            {"key": "max_file_size_mb", "value": "50", "setting_type": "integer", "description": "Maximum file size in MB"},
            {"key": "default_tokens_per_page", "value": "1", "setting_type": "integer", "description": "Default tokens required per page"},
            {"key": "enable_email_notifications", "value": "true", "setting_type": "boolean", "description": "Enable email notifications"},
        ]
        
        for setting_data in settings:
            setting, created = SystemSettings.objects.get_or_create(
                key=setting_data["key"],
                defaults=setting_data
            )
            if created:
                print(f"✅ Created system setting: {setting.key}")
        
        # Create demo user
        demo_user, created = User.objects.get_or_create(
            email="demo@printsmart.com",
            defaults={
                "username": "demo",
                "first_name": "Demo",
                "last_name": "User",
                "tokens": 25,
                "is_email_verified": True
            }
        )
        if created:
            demo_user.set_password("demo123")
            demo_user.save()
            print(f"✅ Created demo user: {demo_user.email} (password: demo123)")
        
        print("\n✅ Sample data setup completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up sample data: {e}")
        return False

def run_tests():
    """Run the test suite"""
    return run_command("python manage.py test", "Running test suite")

def collect_static():
    """Collect static files"""
    return run_command("python manage.py collectstatic --noinput", "Collecting static files")

def check_system():
    """Run Django system checks"""
    return run_command("python manage.py check", "Running system checks")

def create_backup():
    """Create database backup"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{timestamp}.json"
    
    return run_command(
        f"python manage.py dumpdata --indent 2 > {backup_file}",
        f"Creating database backup: {backup_file}"
    )

def restore_backup(backup_file):
    """Restore database from backup"""
    if not os.path.exists(backup_file):
        print(f"❌ Backup file {backup_file} not found!")
        return False
        
    return run_command(
        f"python manage.py loaddata {backup_file}",
        f"Restoring database from: {backup_file}"
    )

def start_celery():
    """Start Celery worker"""
    return run_command(
        "celery -A printsmart_backend worker --loglevel=info",
        "Starting Celery worker"
    )

def start_server():
    """Start Django development server"""
    return run_command(
        "python manage.py runserver",
        "Starting Django development server"
    )

def reset_database():
    """Reset database (WARNING: This will delete all data!)"""
    print("\n⚠️  WARNING: This will delete all data!")
    confirmation = input("Type 'DELETE' to confirm: ")
    
    if confirmation != "DELETE":
        print("❌ Operation cancelled.")
        return False
    
    print("🗑️  Resetting database...")
    
    # Delete database file
    db_file = Path("db.sqlite3")
    if db_file.exists():
        db_file.unlink()
        print("✅ Database file deleted")
    
    # Delete migration files
    for app in ["users", "files", "print_jobs", "payments", "core"]:
        migrations_dir = Path(app) / "migrations"
        if migrations_dir.exists():
            for migration_file in migrations_dir.glob("*.py"):
                if migration_file.name != "__init__.py":
                    migration_file.unlink()
                    print(f"✅ Deleted migration: {migration_file}")
    
    # Recreate migrations and database
    run_command("python manage.py makemigrations", "Creating new migrations")
    run_command("python manage.py migrate", "Creating new database")
    
    print("✅ Database reset completed!")
    return True

def show_urls():
    """Display all URL patterns"""
    return run_command("python manage.py show_urls", "Displaying URL patterns")

def main():
    """Main management interface"""
    print("🖨️  PrintSmart Backend Management")
    print("=" * 50)
    
    while True:
        print("\nAvailable Commands:")
        print("1.  Create Superuser")
        print("2.  Setup Sample Data")
        print("3.  Run Tests")
        print("4.  Collect Static Files")
        print("5.  System Check")
        print("6.  Create Backup")
        print("7.  Restore Backup")
        print("8.  Start Celery Worker")
        print("9.  Start Development Server")
        print("10. Reset Database (DANGER)")
        print("11. Show URLs")
        print("12. Open Django Shell")
        print("0.  Exit")
        
        choice = input("\nEnter your choice (0-12): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            create_superuser()
        elif choice == "2":
            setup_sample_data()
        elif choice == "3":
            run_tests()
        elif choice == "4":
            collect_static()
        elif choice == "5":
            check_system()
        elif choice == "6":
            create_backup()
        elif choice == "7":
            backup_file = input("Enter backup file name: ").strip()
            restore_backup(backup_file)
        elif choice == "8":
            start_celery()
        elif choice == "9":
            start_server()
        elif choice == "10":
            reset_database()
        elif choice == "11":
            show_urls()
        elif choice == "12":
            run_command("python manage.py shell", "Opening Django shell")
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
