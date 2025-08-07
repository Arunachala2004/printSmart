#!/usr/bin/env python
import os
import django
import sqlite3

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')
django.setup()

# Check database schema
db_path = 'db.sqlite3'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table schema
    cursor.execute("PRAGMA table_info(users_user);")
    columns = cursor.fetchall()
    
    print("Current users_user table columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Check if wallet_balance exists
    has_wallet_balance = any('wallet_balance' in str(col) for col in columns)
    print(f"\nwallet_balance column exists: {has_wallet_balance}")
    
    if not has_wallet_balance:
        print("\n🔧 Adding wallet_balance column...")
        try:
            cursor.execute("ALTER TABLE users_user ADD COLUMN wallet_balance DECIMAL(10,2) DEFAULT 0.00;")
            conn.commit()
            print("✅ wallet_balance column added successfully!")
        except Exception as e:
            print(f"❌ Error adding column: {e}")
    
    conn.close()
else:
    print("❌ Database file not found!")
