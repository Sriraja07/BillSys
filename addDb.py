import sqlite3
import csv

# Step 1: Connect to SQLite database (or create it)
conn = sqlite3.connect('my_database.db')
cursor = conn.cursor()

# Step 2: Create a table (adjust columns as per your CSV)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS my_table (
        id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER,
        city TEXT
    )
''')

# Step 3: Open and read the CSV file
with open('static/db.csv', 'r', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)  # Automatically uses headers
    for row in reader:
        cursor.execute('''
            INSERT INTO my_table (name, age, city)
            VALUES (?, ?, ?)
        ''', (row['name'], row['age'], row['city']))

# Step 4: Commit and close
conn.commit()
conn.close()


