import sqlite3


def create_table():
    # Connect to SQLite database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Create table for user credentials if not exists
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT)''')

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_table()
