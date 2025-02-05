import sqlite3
import config

def connect_db():
    return sqlite3.connect(config.DATABASE_NAME, check_same_thread=False)

def create_tables(conn):
    cursor = conn.cursor()
    
    # Создание таблицы пользователей, если она не существует
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        balance REAL DEFAULT 0,
        total_topups REAL DEFAULT 0,
        total_topup_count INTEGER DEFAULT 0,
        total_purchases INTEGER DEFAULT 0
    )
    ''')

    # Создание таблицы товаров, если она не существует
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        file_id TEXT,
        description TEXT
    )
    ''')

    conn.commit()

def update_tables(conn):
    cursor = conn.cursor()

    # Добавление столбцов в таблицу пользователей, если они не существуют
    cursor.execute('PRAGMA table_info(users)')
    columns = [info[1] for info in cursor.fetchall()]
    if 'total_topups' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN total_topups REAL DEFAULT 0')
    if 'total_topup_count' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN total_topup_count INTEGER DEFAULT 0')
    if 'total_purchases' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN total_purchases INTEGER DEFAULT 0')
    
    # Добавление столбца description в таблицу товаров, если он не существует
    cursor.execute('PRAGMA table_info(products)')
    columns = [info[1] for info in cursor.fetchall()]
    if 'description' not in columns:
        cursor.execute('ALTER TABLE products ADD COLUMN description TEXT')
        
    conn.commit()

conn = connect_db()
create_tables(conn)
update_tables(conn)
