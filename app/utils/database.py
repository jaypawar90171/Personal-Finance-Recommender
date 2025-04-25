import sqlite3
import os

def init_db():
    """Initialize the database with required tables if they don't exist"""
    # Create database directory if it doesn't exist
    os.makedirs('database', exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect('database/stock_analyzer.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT,
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP
    )
    ''')
    
    # Create portfolio_items table
    c.execute('''
    CREATE TABLE IF NOT EXISTS portfolio_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticker TEXT NOT NULL,
        shares REAL NOT NULL,
        purchase_price REAL NOT NULL,
        purchase_date TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id, ticker)
    )
    ''')
    
    # Create watchlist_items table
    c.execute('''
    CREATE TABLE IF NOT EXISTS watchlist_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticker TEXT NOT NULL,
        added_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id, ticker)
    )
    ''')
    
    # Create risk_assessments table
    c.execute('''
    CREATE TABLE IF NOT EXISTS risk_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        risk_score REAL NOT NULL,
        risk_profile TEXT NOT NULL,
        risk_description TEXT,
        created_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create selected_stocks table
    c.execute('''
    CREATE TABLE IF NOT EXISTS selected_stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticker TEXT NOT NULL,
        added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id, ticker)
    )
    ''')
    
    # Create user_settings table
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        theme TEXT DEFAULT 'light',
        email_notifications INTEGER DEFAULT 1,
        price_alerts INTEGER DEFAULT 1,
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id)
    )
    ''')
    
    # Create chat_messages table
    c.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        is_user INTEGER NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create demo user if it doesn't exist
    c.execute("SELECT id FROM users WHERE username = 'demo_user'")
    if not c.fetchone():
        import hashlib
        hashed_password = hashlib.sha256('demo123'.encode()).hexdigest()
        
        c.execute('''
        INSERT INTO users (username, password, email, full_name, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        ''', ('demo_user', hashed_password, 'demo@example.com', 'Demo User'))
    
    conn.commit()
    conn.close()
