import os
import pandas as pd
import sqlite3

# List of (csv_path, db_path, table_name)
files = [
    ("NCERT_Biology_11th/Biology_11th_Cleaned.csv", "NCERT_Biology_11th/Biology_11th_Cleaned.sqlite", "Biology_11th_Cleaned"),
    ("NCERT_Biology_12th/Biology_12th_Cleaned.csv", "NCERT_Biology_12th/Biology_12th_Cleaned.sqlite", "Biology_12th_Cleaned"),
    ("NCERT_Chemistry_11th/Chemsitry_11th_Cleaned.csv", "NCERT_Chemistry_11th/Chemsitry_11th_Cleaned.sqlite", "Chemsitry_11th_Cleaned"),
    ("NCERT_Chemistry_12th/Chemsitry_12th_Cleaned.csv", "NCERT_Chemistry_12th/Chemsitry_12th_Cleaned.sqlite", "Chemsitry_12th_Cleaned"),
    ("NCERT_Physics_11th/Physics_11th_Cleaned.csv", "NCERT_Physics_11th/Physics_11th_Cleaned.sqlite", "Physics_11th_Cleaned"),
    ("NCERT_Physics_12th/Physics_12th_Cleaned.csv", "NCERT_Physics_12th/Physics_12th_Cleaned.sqlite", "Physics_12th_Cleaned"),
]

for csv_path, db_path, table_name in files:
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        continue
    print(f"Processing {csv_path} -> {db_path} (table: {table_name})")
    df = pd.read_csv(csv_path)
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    print(f"Created {db_path}")

print("All CSV files have been converted to SQLite databases.")
