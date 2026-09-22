import sqlite3

conn = sqlite3.connect("agrilink.db")

cursor = conn.cursor()

print("Tables:")
print(cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall())

print("\nUsers Table:")
try:
    print(cursor.execute("SELECT * FROM users;").fetchall())
except Exception as e:
    print(e)

conn.close()