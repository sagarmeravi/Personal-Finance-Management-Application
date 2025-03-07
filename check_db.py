import sqlite3

conn = sqlite3.connect('finance_app.db')
cursor = conn.cursor()

# Show tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

# Show data from users table
cursor.execute("SELECT * FROM users;")
print("Users:", cursor.fetchall())

conn.close()
