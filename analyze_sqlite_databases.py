import sqlite3
import os

db_files = [
    "NCERT_Biology_11th/Biology_11th_Cleaned.sqlite",
    "NCERT_Biology_12th/Biology_12th_Cleaned.sqlite",
    "NCERT_Chemistry_11th/Chemsitry_11th_Cleaned.sqlite",
    "NCERT_Chemistry_12th/Chemsitry_12th_Cleaned.sqlite",
    "NCERT_Physics_11th/Physics_11th_Cleaned.sqlite",
    "NCERT_Physics_12th/Physics_12th_Cleaned.sqlite",
]

def analyze_db(db_path):
    print(f"\n=== Database: {db_path} ===")
    if not os.path.exists(db_path):
        print("File not found.")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    if not tables:
        print("No tables found.")
        conn.close()
        return
    for table in tables:
        print(f"\n--- Table: {table} ---")
        # Schema
        cursor.execute(f"PRAGMA table_info({table})")
        schema = cursor.fetchall()
        print("Schema:")
        for col in schema:
            print(f"  {col[1]} ({col[2]})")
        # Row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Total rows: {count}")
        # Sample rows
        cursor.execute(f"SELECT * FROM {table} LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            print("Sample rows:")
            for row in rows:
                print("  ", row)
        else:
            print("No data in table.")
    conn.close()

if __name__ == "__main__":
    for db in db_files:
        analyze_db(db)
