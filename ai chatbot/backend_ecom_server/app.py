# backend_ecom_server/app.py

from flask import Flask, request, jsonify, g
from flask_cors import CORS # Needed for cross-origin requests from your HTML file
import uuid
import datetime
from database import get_db, close_db, init_app # Import database functions

app = Flask(__name__)
CORS(app) # Enable CORS for all routes so our frontend can talk to it

init_app(app) # Initialize database functions with the Flask app

# --- Helper Functions for Database Interaction ---
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cursor = db.execute(query, args)
    db.commit()
    return cursor

# --- API Endpoints ---

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = query_db("SELECT * FROM users WHERE username = ? AND password = ?", (username, password), one=True)
    if user:
        # In a real app, you'd generate a secure token (JWT) here
        session_id = str(uuid.uuid4()) # A simple mock session ID for demonstration
        # Store session_id linked to user if needed, or simply return it
        return jsonify({"message": "Login successful", "user_id": user['id'], "session_id": session_id}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/products', methods=['GET'])
def get_products():
    search_query = request.args.get('q', '').lower()
    category = request.args.get('category', '').lower()
    brand = request.args.get('brand', '').lower()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    product_id = request.args.get('id') # To get specific product by ID via query param

    products = []
    if product_id:
        product = query_db("SELECT * FROM products WHERE id = ?", (product_id,), one=True)
        if product:
            products.append(dict(product))
    else:
        # Build dynamic query based on filters
        query = "SELECT * FROM products WHERE 1=1"
        params = []
        if search_query:
            query += " AND (LOWER(name) LIKE ? OR LOWER(description) LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        if category:
            query += " AND LOWER(category) = ?"
            params.append(category)
        if brand:
            query += " AND LOWER(brand) = ?"
            params.append(brand)
        if min_price is not None:
            query += " AND price >= ?"
            params.append(min_price)
        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)

        all_products = query_db(query, params)
        products = [dict(p) for p in all_products]

    return jsonify({"products": products})

@app.route('/products/<product_id>', methods=['GET'])
def get_product_details(product_id):
    product = query_db("SELECT * FROM products WHERE id = ?", (product_id,), one=True)
    if product:
        return jsonify(dict(product))
    return jsonify({"error": "Product not found"}), 404

@app.route('/cart/<user_id>', methods=['GET'])
def view_cart(user_id):
    # Find the cart for the given user
    cart = query_db("SELECT id FROM carts WHERE user_id = ?", (user_id,), one=True)
    if not cart:
        # Create a cart if one doesn't exist for this user (should be created at user creation)
        cart_id = str(uuid.uuid4())
        execute_db("INSERT INTO carts (id, user_id) VALUES (?, ?)", (cart_id, user_id))
        return jsonify({"items": [], "total_price": 0.0}), 200 # Return empty cart

    cart_id = cart['id']
    cart_items = query_db("""
        SELECT ci.id as item_id, p.id as product_id, p.name, p.price, ci.quantity, p.image_url
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.cart_id = ?
    """, (cart_id,))

    items = [dict(item) for item in cart_items]
    total_price = sum(item['price'] * item['quantity'] for item in items)
    return jsonify({"items": items, "total_price": total_price})

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not user_id or not product_id or not quantity:
        return jsonify({"error": "User ID, Product ID, and Quantity are required"}), 400

    product = query_db("SELECT * FROM products WHERE id = ?", (product_id,), one=True)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    if product['stock'] < quantity:
        return jsonify({"error": f"Not enough stock for {product['name']}. Only {product['stock']} available."}), 400

    cart = query_db("SELECT id FROM carts WHERE user_id = ?", (user_id,), one=True)
    if not cart: # Should ideally be created upon user creation/login
        cart_id = str(uuid.uuid4())
        execute_db("INSERT INTO carts (id, user_id) VALUES (?, ?)", (cart_id, user_id))
    else:
        cart_id = cart['id']

    # Check if product already in cart
    cart_item = query_db("SELECT * FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart_id, product_id), one=True)

    if cart_item:
        new_quantity = cart_item['quantity'] + quantity
        execute_db("UPDATE cart_items SET quantity = ? WHERE id = ?", (new_quantity, cart_item['id']))
        message = f"{quantity} more of {product['name']} added to cart."
    else:
        cart_item_id = str(uuid.uuid4())
        execute_db("INSERT INTO cart_items (id, cart_id, product_id, quantity) VALUES (?, ?, ?, ?)",
                   (cart_item_id, cart_id, product_id, quantity))
        message = f"{quantity} x {product['name']} added to cart."

    # Update stock in products table
    execute_db("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))

    return jsonify({"message": message}), 200

@app.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    remove_quantity = data.get('quantity', -1) # -1 means remove all

    if not user_id or not product_id:
        return jsonify({"error": "User ID and Product ID are required"}), 400

    cart = query_db("SELECT id FROM carts WHERE user_id = ?", (user_id,), one=True)
    if not cart:
        return jsonify({"error": "Cart not found for this user"}), 404
    cart_id = cart['id']

    cart_item = query_db("SELECT * FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart_id, product_id), one=True)
    if not cart_item:
        return jsonify({"error": "Product not found in cart"}), 404

    current_quantity = cart_item['quantity']
    quantity_to_return_to_stock = 0

    if remove_quantity == -1 or remove_quantity >= current_quantity:
        # Remove all
        quantity_to_return_to_stock = current_quantity
        execute_db("DELETE FROM cart_items WHERE id = ?", (cart_item['id'],))
        message = f"All {current_quantity} units of {cart_item['product_id']} removed from cart."
    else:
        # Remove specific quantity
        new_quantity = current_quantity - remove_quantity
        quantity_to_return_to_stock = remove_quantity
        execute_db("UPDATE cart_items SET quantity = ? WHERE id = ?", (new_quantity, cart_item['id']))
        message = f"{remove_quantity} units of {cart_item['product_id']} removed from cart. New quantity: {new_quantity}."

    # Return stock to products table
    execute_db("UPDATE products SET stock = stock + ? WHERE id = ?", (quantity_to_return_to_stock, product_id))

    return jsonify({"message": message}), 200

@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    cart = query_db("SELECT id FROM carts WHERE user_id = ?", (user_id,), one=True)
    if not cart:
        return jsonify({"error": "Cart not found for this user"}), 404
    cart_id = cart['id']

    cart_items = query_db("""
        SELECT ci.product_id, p.name, p.price, ci.quantity
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.cart_id = ?
    """, (cart_id,))

    if not cart_items:
        return jsonify({"error": "Your cart is empty. Nothing to checkout."}), 400

    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
    order_id = str(uuid.uuid4())
    order_date = datetime.datetime.now().isoformat()
    status = 'pending'

    # Insert into orders table
    execute_db("INSERT INTO orders (id, user_id, order_date, total_amount, status) VALUES (?, ?, ?, ?, ?)",
               (order_id, user_id, order_date, total_amount, status))

    # Insert into order_items and clear cart items
    for item in cart_items:
        order_item_id = str(uuid.uuid4())
        execute_db("INSERT INTO order_items (id, order_id, product_id, quantity, price_at_purchase) VALUES (?, ?, ?, ?, ?)",
                   (order_item_id, order_id, item['product_id'], item['quantity'], item['price']))
        execute_db("DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart_id, item['product_id']))

    return jsonify({"message": "Order placed successfully!", "order_id": order_id, "total_amount": total_amount}), 200

@app.route('/chat_logs', methods=['POST'])
def add_chat_log():
    data = request.get_json()
    session_id = data.get('session_id')
    sender = data.get('sender')
    message = data.get('message')
    timestamp = datetime.datetime.now().isoformat()

    if not session_id or not sender or not message:
        return jsonify({"error": "Session ID, sender, and message are required"}), 400

    log_id = str(uuid.uuid4())
    execute_db("INSERT INTO chat_logs (id, session_id, sender, message, timestamp) VALUES (?, ?, ?, ?, ?)",
               (log_id, session_id, sender, message, timestamp))
    return jsonify({"message": "Chat log recorded"}), 201

if __name__ == '__main__':
    # Make sure to run mock_data.py first to initialize the database
    print("Running Flask E-commerce Server...")
    app.run(debug=True, port=5000) # Runs on http://localhost:5000