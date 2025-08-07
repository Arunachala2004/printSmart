#!/usr/bin/env python
"""
Comprehensive database fix for PrintSmart wallet_balance column issue
"""
import os
import sqlite3

def fix_wallet_balance_column():
    """Add wallet_balance column to users_user table"""
    db_path = 'db.sqlite3'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(users_user);")
        columns = cursor.fetchall()
        
        # Check if wallet_balance exists
        has_wallet_balance = any('wallet_balance' in str(col[1]) for col in columns)
        
        if not has_wallet_balance:
            print("🔧 Adding wallet_balance column...")
            
            # Add the column
            cursor.execute("""
                ALTER TABLE users_user 
                ADD COLUMN wallet_balance DECIMAL(10,2) DEFAULT 0.00;
            """)
            
            # Update all existing users to have a default balance
            cursor.execute("""
                UPDATE users_user 
                SET wallet_balance = 100.00 
                WHERE wallet_balance IS NULL OR wallet_balance = 0;
            """)
            
            conn.commit()
            print("✅ wallet_balance column added and users updated!")
            
        else:
            print("✅ wallet_balance column already exists")
        
        # Verify the schema
        cursor.execute("PRAGMA table_info(users_user);")
        columns = cursor.fetchall()
        
        print("\nFinal table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Show sample data
        cursor.execute("SELECT username, wallet_balance FROM users_user LIMIT 3;")
        users = cursor.fetchall()
        
        print("\nSample user data:")
        for user in users:
            print(f"  - {user[0]}: ${user[1] or 0.00}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_missing_superuser():
    """Create superuser if none exists"""
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')
        django.setup()
        
        from users.models import User
        
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@printsmart.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                wallet_balance=1000.00
            )
            print("✅ Superuser created: admin/admin123")
        else:
            print("✅ Superuser already exists")
            
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")

def main():
    print("🚀 PrintSmart Database Fix Script")
    print("=" * 40)
    
    # Fix the database schema
    if fix_wallet_balance_column():
        print("\n🔧 Database schema fixed!")
        
        # Create superuser
        create_missing_superuser()
        
        print("\n🎉 All fixes completed successfully!")
        print("You can now restart the Django server:")
        print("  python manage.py runserver")
        
    else:
        print("\n❌ Database fix failed!")

if __name__ == '__main__':
    main()
