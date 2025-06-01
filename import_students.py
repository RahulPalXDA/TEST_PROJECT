import csv
import sqlite3
import os

CSV_FILENAME = 'data.csv'
DB_FILENAME = 'database.db'

def main():
    if not os.path.isfile(CSV_FILENAME):
        print(f"CSV file '{CSV_FILENAME}' not found.")
        return
    if not os.path.isfile(DB_FILENAME):
        print(f"Database file '{DB_FILENAME}' not found. Please run db.py first.")
        return

    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    with open(CSV_FILENAME, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            username = row['Student Name'].strip()
            password = 'defaultpassword'
            try:
                c.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, 'student')",
                    (username, password)
                )
            except sqlite3.IntegrityError:
                # User already exists
                pass
            c.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_id_row = c.fetchone()
            if not user_id_row:
                continue
            user_id = user_id_row[0]
            # Clean annual income
            income_str = row['Annual Income (₹)'].replace(',', '').replace('₹', '').strip()
            try:
                annual_income = int(income_str)
            except ValueError:
                annual_income = 0
            c.execute(
                '''REPLACE INTO profiles 
                   (user_id, full_name, annual_income, hometown, college_name, college_location)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    user_id,
                    row['Student Name'].strip(),
                    annual_income,
                    row['Hometown'].strip(),
                    row['College Name'].strip(),
                    row['College Location'].strip()
                )
            )
            count += 1
    conn.commit()
    conn.close()
    print(f"Imported {count} students from '{CSV_FILENAME}' into '{DB_FILENAME}'.")

if __name__ == '__main__':
    main()