#!/usr/bin/env python
import sqlite3
import os

db_path = 'db.sqlite3'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Available tables in database:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check if any user-related tables exist
    user_tables = [t[0] for t in tables if 'user' in t[0].lower()]
    
    if user_tables:
        print(f"\nUser-related tables: {user_tables}")
        
        # Check schema of first user table
        table_name = user_tables[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        print(f"\nSchema of {table_name}:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    
    conn.close()
else:
    print("❌ Database file doesn't exist!")
