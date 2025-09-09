import sqlite3
import csv

# Connect to your SQLite database
conn = sqlite3.connect('my_database.db')
cursor = conn.cursor()

# Name of the table you want to export
table_name = 'my_table'

# Query all data from the table
cursor.execute(f"SELECT * FROM {table_name}")
rows = cursor.fetchall()

# Get column names
column_names = [description[0] for description in cursor.description]

# Write to CSV
with open('exported_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(column_names)  # Write header
    writer.writerows(rows)         # Write data rows

# Close the connection
conn.close()

print("Export complete: 'exported_data.csv'")
