import sqlite3
from config import DATABASE_URL

def get_db_connection():
    conn = sqlite3.connect('service_bot.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create services table
    c.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    ''')
    
    # Create orders table
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (service_id) REFERENCES services (id)
        )
    ''')

    # Create channels table
    c.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            invite_link TEXT NOT NULL
        )
    ''')

    # Create users table for broadcasting, balance, and referrals
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance REAL DEFAULT 0.0,
            referred_by INTEGER,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Migrations
    try:
        c.execute('ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0.0')
    except:
        pass # Column likely exists
    
    try:
        c.execute('ALTER TABLE users ADD COLUMN referred_by INTEGER')
    except:
        pass # Column likely exists
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
