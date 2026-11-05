import sqlite3
import pandas as pd

# 1. Connect to a new database file (this creates it if it doesn't exist)
conn = sqlite3.connect('database.sqlite')

# 2. Read your CSV file (replace 'student_data.csv' with your actual file name)
# Assuming your CSV has columns like: college_id, name, placement_score, etc.
df = pd.read_csv('Final-Database.csv.xls')

# 3. Save the data into the SQLite database as a table named 'colleges'
df.to_sql('colleges', conn, if_exists='replace', index=False)

print("Database created successfully!")

# 4. Close the connection
conn.close()