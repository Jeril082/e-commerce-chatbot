# backend_ecom_server/database.py

import sqlite3
from flask import g # 'g' is a special object in Flask for storing data during a request

DATABASE = 'ecom_data.db' # Our database file will be named ecom_data.db

def get_db():
    """Establishes a database connection or returns the existing one."""
    if 'db' not in g: # Check if a database connection already exists for the current request
        g.db = sqlite3.connect(DATABASE) # If not, create one
        g.db.row_factory = sqlite3.Row # This makes rows behave like dictionaries (access columns by name)
    return g.db # Return the connection

def close_db(e=None):
    """Closes the database connection."""
    db = g.pop('db', None) # Get the db connection from 'g' and remove it

    if db is not None:
        db.close() # Close the connection

def init_db():
    """Initializes the database schema."""
    db = get_db() # Get a database connection
    with app.open_resource('schema.sql') as f: # Open schema.sql (we'll create this next)
        db.executescript(f.read().decode('utf8')) # Execute SQL commands from the schema file

def init_app(app_instance):
    """Registers database functions with the Flask app."""
    global app # Make Flask app instance accessible globally for init_db
    app = app_instance
    app.teardown_appcontext(close_db) # Ensure db connection is closed after each request
    # No need to call init_db here directly, it will be called by mock_data.py or manually

if __name__ == '__main__':
    # This block allows you to run this file directly to initialize the db
    # In a real app, this would be part of a proper setup script or Flask CLI command
    # For simplicity, we'll trigger init_db from mock_data.py
    print("Database functions defined. Run mock_data.py to initialize and populate.")