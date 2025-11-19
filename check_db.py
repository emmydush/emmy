import sqlite3
import os

# Check if db.sqlite3 exists
if os.path.exists("db.sqlite3"):
    print("Database file exists")
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    # Check if the settings_businesssettings table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='settings_businesssettings'"
    )
    result = cursor.fetchone()
    print(f"settings_businesssettings table exists: {result is not None}")

    if result:
        # Try to query the table
        try:
            cursor.execute("SELECT COUNT(*) FROM settings_businesssettings")
            count = cursor.fetchone()[0]
            print(f"Number of records in settings_businesssettings: {count}")
        except Exception as e:
            print(f"Error querying table: {e}")
    else:
        print("settings_businesssettings table does not exist")

    conn.close()
else:
    print("Database file does not exist")
