import sqlite3
import os

db_path = 'db.sqlite3'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Adding 'status' column to 'events_event' table...")
try:
    # Add the column with a default value
    cursor.execute("ALTER TABLE events_event ADD COLUMN status varchar(20) NOT NULL DEFAULT 'draft'")
    conn.commit()
    print("Column 'status' added successfully.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("Column 'status' already exists.")
    else:
        print(f"Error: {e}")
except Exception as e:
    print(f"Error: {e}")

conn.close()
