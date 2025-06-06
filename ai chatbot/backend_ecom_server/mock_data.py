# backend_ecom_server/mock_data.py

import sqlite3
import uuid
import pandas as pd
from faker import Faker # For generating fake data
from database import DATABASE, init_db # Import from our database setup

# Temporarily create a mock Flask app context for init_db to work
class MockApp:
    def open_resource(self, path):
        # Simulate app.open_resource to read schema.sql
        return open(path, 'rb')
    def teardown_appcontext(self, func):
        pass # Do nothing for mock app

mock_app_instance = MockApp()
# Initialize database schema first
conn = sqlite3.connect(DATABASE)
with open('schema.sql', 'r') as f:
    conn.executescript(f.read())
conn.close()


fake = Faker()

def generate_mock_products(num_products=100):
    """Generates mock product data."""
    products = []
    categories = ['Electronics', 'Home & Kitchen', 'Books', 'Clothing', 'Sports', 'Beauty']
    brands = ['TechGen', 'HomeLux', 'PageTurner', 'FashionFlow', 'FitLife', 'GlowUp']

    for _ in range(num_products):
        product_id = str(uuid.uuid4())
        name = fake.word().capitalize() + " " + fake.word().capitalize() + " " + fake.random_element(['Pro', 'Max', 'Lite', 'Edition', 'Basic'])
        description = fake.sentence(nb_words=10)
        price = round(fake.random_element([19.99, 49.99, 99.99, 149.99, 199.99, 299.99, 499.99, 799.99]), 2)
        category = fake.random_element(categories)
        brand = fake.random_element(brands)
        stock = fake.random_int(min=0, max=200) # Some products can be out of stock
        image_url = f"https://via.placeholder.com/150?text={name.replace(' ', '+')}" # Placeholder image

        products.append((product_id, name, description, price, category, brand, stock, image_url))
    return products

def populate_db():
    """Populates the database with mock products and a user."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM products")
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM carts")
    cursor.execute("DELETE FROM cart_items")
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM order_items")
    cursor.execute("DELETE FROM chat_logs") # Clear chat logs too

    # Insert products
    products_data = generate_mock_products()
    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?)", products_data)
    print(f"Inserted {len(products_data)} mock products.")

    # Insert a mock user
    user_id = "test_user_123"
    username = "testuser"
    password = "password" # In a real app, hash this password!
    cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (user_id, username, password))
    print(f"Inserted mock user: {username}")

    # Create an empty cart for the mock user
    cart_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO carts VALUES (?, ?)", (cart_id, user_id))
    print(f"Created empty cart for {username}")

    conn.commit()
    conn.close()
    print("Database populated successfully!")

if __name__ == '__main__':
    populate_db()