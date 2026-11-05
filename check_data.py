import sqlite3
import pandas as pd

# Connect to the database we just made
conn = sqlite3.connect('database.sqlite')

# Get just the first row of data to see the structure
df = pd.read_sql("SELECT * FROM colleges LIMIT 1", conn)

# Print out the exact names of all the columns
print("YOUR EXACT COLUMN NAMES ARE:")
print(df.columns.tolist())

conn.close()