#!/usr/bin/env python
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Update admin wallet balance
cursor.execute("UPDATE users SET wallet_balance = 1000.00 WHERE username = 'admin';")
conn.commit()

# Verify the update
cursor.execute("SELECT username, wallet_balance FROM users WHERE username = 'admin';")
result = cursor.fetchone()

if result:
    print(f"✅ Admin wallet balance updated: {result[0]} = ${result[1]}")
else:
    print("❌ Admin user not found")

conn.close()
