import sqlite3
import os

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Create a sample database with customer data
conn = sqlite3.connect('data/customers.db')
cursor = conn.cursor()

# Create customers table
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    status TEXT,
    account_balance REAL,
    join_date TEXT
)
''')

# Create orders table
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    order_number TEXT,
    product TEXT,
    amount REAL,
    status TEXT,
    order_date TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers (id)
)
''')

# Insert sample customer data
customers_data = [
    ('John Doe', 'john.doe@email.com', '555-0101', 'Active', 1500.00, '2024-01-15'),
    ('Jane Smith', 'jane.smith@email.com', '555-0102', 'Active', 2300.50, '2024-02-20'),
    ('Bob Johnson', 'bob.johnson@email.com', '555-0103', 'Inactive', 0.00, '2023-11-10'),
    ('Alice Brown', 'alice.brown@email.com', '555-0104', 'Active', 750.25, '2024-03-05'),
    ('Charlie Wilson', 'charlie.wilson@email.com', '555-0105', 'Active', 3200.00, '2024-01-08'),
]

cursor.executemany(
    'INSERT INTO customers (name, email, phone, status, account_balance, join_date) VALUES (?, ?, ?, ?, ?, ?)',
    customers_data
)

# Insert sample orders
orders_data = [
    (1, 'ORD-001', 'Laptop', 1200.00, 'Delivered', '2024-01-20'),
    (1, 'ORD-002', 'Mouse', 25.00, 'Delivered', '2024-02-15'),
    (2, 'ORD-003', 'Monitor', 450.00, 'Shipped', '2024-10-28'),
    (2, 'ORD-004', 'Keyboard', 85.00, 'Processing', '2024-11-05'),
    (4, 'ORD-005', 'Headphones', 150.00, 'Delivered', '2024-03-10'),
    (5, 'ORD-006', 'Desk', 320.00, 'Shipped', '2024-11-01'),
]

cursor.executemany(
    'INSERT INTO orders (customer_id, order_number, product, amount, status, order_date) VALUES (?, ?, ?, ?, ?, ?)',
    orders_data
)

conn.commit()
conn.close()

print("✅ Database created successfully!")
print("Created 'data/customers.db' with sample data:")
print("- 5 customers")
print("- 6 orders")
