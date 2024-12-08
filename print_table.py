import sqlite3

# Path to the betbuddy.db file
db_file = 'bettingBuddy.db'

# Connect to the SQLite database
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Query to fetch all table names in the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Iterate through each table and fetch all rows
for table in tables:
    table_name = table[0]
    print(f"Contents of table: {table_name}")

    # Query to fetch all rows from the table
    cursor.execute(f"SELECT * FROM {table_name};")
    rows = cursor.fetchall()

    # Print column names
    columns = [description[0] for description in cursor.description]
    print("Columns:", columns)

    # Print each row
    for row in rows:
        print(row)
    print("-" * 50)

# Close the connection
conn.close()

