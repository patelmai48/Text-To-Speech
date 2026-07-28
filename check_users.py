import sqlite3
import os

db_path = os.path.join('instance', 'database.db')

if not os.path.exists(db_path):
    db_path = 'database.db'

if not os.path.exists(db_path):
    print("Database file not found!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Query users and count their histories
    query = """
        SELECT 
            u.id, 
            u.username, 
            u.email, 
            u.created_at, 
            u.last_login, 
            u.email_verified,
            COUNT(h.id) AS conversion_count
        FROM users u
        LEFT JOIN histories h ON u.id = h.user_id
        GROUP BY u.id
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print("=" * 80)
    print(f"{'USER DATABASE SUMMARY':^80}")
    print("=" * 80)
    print(f"Total Users Registered: {len(rows)}")
    print("-" * 80)
    
    for row in rows:
        user_id, username, email, created, last_login, verified, conversions = row
        status = "Verified" if verified else "Unverified"
        print(f"User ID: {user_id}")
        print(f"  Username:    {username}")
        print(f"  Email:       {email}")
        print(f"  Created:     {created}")
        print(f"  Last Login:  {last_login}")
        print(f"  Status:      {status}")
        print(f"  Conversions: {conversions} scripts synthesized")
        print("-" * 80)
        
except sqlite3.OperationalError as e:
    print("Error reading database:", e)
finally:
    conn.close()
