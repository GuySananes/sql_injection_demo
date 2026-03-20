# database.py
# This file is responsible for setting up the SQLite database and seeding it
# with a test user. It runs once before the app starts.

import sqlite3  # sqlite3 is built into Python — no installation needed


def init_db():
    """
    Creates the database file, builds the users table, and inserts a test user.
    SQLite automatically creates the .db file if it doesn't exist yet.
    """

    # Connecting to a .db file creates it on disk if it doesn't already exist
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()  # cursor is used to execute SQL commands

    # CREATE TABLE IF NOT EXISTS: safe to run multiple times — won't crash
    # if the table already exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- unique ID, auto-incremented
            username TEXT NOT NULL,                -- login username
            password TEXT NOT NULL                 -- login password (plaintext for demo purposes)
        )
    """)

    # Only seed if the table is empty — avoids wiping data on every restart
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:

        # Only seed if the table is empty — avoids wiping data on every restart
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                [
                    ("admin", "password123"),
                    ("alice", "qwerty456"),
                    ("bob", "letmein789"),
                ]
            )

    # commit() saves the changes to disk — without this, nothing is persisted
    conn.commit()

    # Always close the connection when done to free up resources
    conn.close()

    print("Database initialized with test user: admin / password123")


# This block only runs if you execute this file directly: `python database.py`
# It will NOT run when database.py is imported by app.py
if __name__ == "__main__":
    init_db()