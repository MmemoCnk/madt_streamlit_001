import os
import psycopg2
from psycopg2.extras import DictCursor

def get_db_connection():
    """Create a connection to the PostgreSQL database"""
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'postgres'),
        database=os.environ.get('DB_NAME', 'restaurant'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgres')
    )
    return conn

def initialize_database():
    """Create database tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create menu_items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        price NUMERIC(10, 2) NOT NULL,
        category VARCHAR(50) NOT NULL
    )
    ''')
    
    # Create members table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS members (
        member_id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        phone VARCHAR(20) NOT NULL,
        points INTEGER DEFAULT 0
    )
    ''')
    
    # Create favorite_items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS favorite_items (
        member_id VARCHAR(50) REFERENCES members(member_id),
        menu_item_id INTEGER REFERENCES menu_items(id),
        count INTEGER DEFAULT 0,
        PRIMARY KEY (member_id, menu_item_id)
    )
    ''')
    
    # Create orders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id VARCHAR(50) PRIMARY KEY,
        customer_id VARCHAR(50),
        total_amount NUMERIC(10, 2) NOT NULL,
        status VARCHAR(20) NOT NULL,
        timestamp TIMESTAMP NOT NULL
    )
    ''')
    
    # Create order_items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        order_id VARCHAR(50) REFERENCES orders(order_id),
        menu_item_id INTEGER REFERENCES menu_items(id),
        PRIMARY KEY (order_id, menu_item_id)
    )
    ''')
    
    # Create member_allergies table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS member_allergies (
        allergy_id INTEGER PRIMARY KEY,
        member_id VARCHAR(50) REFERENCES members(member_id),
        allergen VARCHAR(100) NOT NULL,
        severity VARCHAR(20) NOT NULL
    )
    ''')
    
    # Create menu_allergens table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS menu_allergens (
        menu_item_id INTEGER REFERENCES menu_items(id),
        allergen VARCHAR(100) NOT NULL,
        PRIMARY KEY (menu_item_id, allergen)
    )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

# Initialize the database when module is imported
initialize_database()