import sqlite3
import os

DB_CONFIG = [
    # (subject, grade, db_path, table_name)
    ("Biology", "11", "NCERT_Biology_11th/Biology_11th_Cleaned.sqlite", "Biology_11th_Cleaned"),
    ("Biology", "12", "NCERT_Biology_12th/Biology_12th_Cleaned.sqlite", "Biology_12th_Cleaned"),
    ("Chemistry", "11", "NCERT_Chemistry_11th/Chemsitry_11th_Cleaned.sqlite", "Chemsitry_11th_Cleaned"),
    ("Chemistry", "12", "NCERT_Chemistry_12th/Chemsitry_12th_Cleaned.sqlite", "Chemsitry_12th_Cleaned"),
    ("Physics", "11", "NCERT_Physics_11th/Physics_11th_Cleaned.sqlite", "Physics_11th_Cleaned"),
    ("Physics", "12", "NCERT_Physics_12th/Physics_12th_Cleaned.sqlite", "Physics_12th_Cleaned"),
]

difficulties = ["Easy", "Medium", "Hard"]

def main():
    report_lines = []
    for subject, grade, db_path, table in DB_CONFIG:
        if not os.path.exists(db_path):
            report_lines.append(f"DB missing: {db_path}")
            continue
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Get all topics
        try:
            cursor.execute(f"SELECT DISTINCT Topic FROM {table}")
            topics = [row[0] for row in cursor.fetchall() if row[0]]
        except Exception as e:
            report_lines.append(f"Error reading topics from {db_path}: {e}")
            conn.close()
            continue
        for topic in topics:
            for diff in difficulties:
                try:
                    cursor.execute(
                        f"SELECT COUNT(*) FROM {table} WHERE Topic=? AND Difficulty=?",
                        (topic, diff)
                    )
                    count = cursor.fetchone()[0]
                    report_lines.append(
                        f"{subject} | Grade {grade} | Topic: {topic} | Difficulty: {diff} | Count: {count}"
                    )
                except Exception as e:
                    report_lines.append(
                        f"Error counting for {subject} {grade} {topic} {diff}: {e}"
                    )
        conn.close()
    # Output to file and console
    with open("question_count_report.txt", "w", encoding="utf-8") as f:
        for line in report_lines:
            print(line)
            f.write(line + "\n")

if __name__ == "__main__":
    main()
