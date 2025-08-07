#!/usr/bin/env python
import sqlite3
import os

def fix_users_table():
    """Fix the users table by adding wallet_balance column"""
    db_path = 'db.sqlite3'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema of users table
        cursor.execute("PRAGMA table_info(users);")
        columns = cursor.fetchall()
        
        print("Current users table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Check if wallet_balance exists
        has_wallet_balance = any('wallet_balance' in str(col[1]) for col in columns)
        
        if not has_wallet_balance:
            print("\n🔧 Adding wallet_balance column to users table...")
            
            cursor.execute("ALTER TABLE users ADD COLUMN wallet_balance DECIMAL(10,2) DEFAULT 100.00;")
            conn.commit()
            
            print("✅ wallet_balance column added successfully!")
        else:
            print("✅ wallet_balance column already exists")
        
        # Update existing users
        cursor.execute("UPDATE users SET wallet_balance = 100.00 WHERE wallet_balance IS NULL;")
        conn.commit()
        
        # Show sample data
        cursor.execute("SELECT username, wallet_balance FROM users LIMIT 3;")
        users = cursor.fetchall()
        
        print("\nUser data:")
        for user in users:
            print(f"  - {user[0]}: ${user[1] or 0.00}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    print("🔧 Fixing users table...")
    if fix_users_table():
        print("\n🎉 Users table fixed successfully!")
    else:
        print("\n❌ Failed to fix users table")
