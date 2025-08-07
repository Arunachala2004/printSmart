#!/usr/bin/env python
import os
import django
import sqlite3

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')
django.setup()

def fix_database():
    """Fix the database by adding the missing wallet_balance column"""
    db_path = 'db.sqlite3'
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if wallet_balance column exists
        cursor.execute("PRAGMA table_info(users_user);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("Current columns in users_user table:")
        for name in column_names:
            print(f"  - {name}")
        
        if 'wallet_balance' not in column_names:
            print("\n🔧 Adding wallet_balance column...")
            
            # Add the column
            cursor.execute("ALTER TABLE users_user ADD COLUMN wallet_balance DECIMAL(10,2) DEFAULT 0.00;")
            conn.commit()
            
            print("✅ wallet_balance column added successfully!")
            
            # Update existing users to have a default balance
            cursor.execute("UPDATE users_user SET wallet_balance = 100.00 WHERE wallet_balance IS NULL;")
            conn.commit()
            
            print("✅ Updated existing users with default wallet balance")
            
        else:
            print("✅ wallet_balance column already exists")
        
        # Verify the fix
        cursor.execute("SELECT username, wallet_balance FROM users_user LIMIT 5;")
        users = cursor.fetchall()
        
        print("\nCurrent users and their wallet balances:")
        for user in users:
            print(f"  - {user[0]}: ${user[1]}")
        
        conn.close()
        print("\n🎉 Database fix completed successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_database()
