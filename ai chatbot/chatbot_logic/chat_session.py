# chatbot_logic/chat_session.py

import uuid
import datetime

class ChatSession:
    """Manages the state and history for a single user's chat session."""
    _sessions = {} # A dictionary to store all active sessions (in a real app, this would be a database)

    def __init__(self, user_id="guest"):
        self.session_id = str(uuid.uuid4()) # Unique ID for this chat session
        self.user_id = user_id # Link to a user (can be 'guest' or a logged-in user ID)
        self.chat_history = [] # List to store messages: [{"sender": "user/chatbot", "message": "text", "timestamp": "..."}]
        self.context = { # Stores relevant information for the conversation
            "last_searched_products": [], # List of products from the last search
            "last_viewed_product_id": None,
            "current_flow": None, # e.g., "search_flow", "checkout_flow"
            "logged_in": False,
            "username": None,
            "session_token": None # Token received from e-commerce server
        }
        self.start_time = datetime.datetime.now() # When the session started
        ChatSession._sessions[self.session_id] = self # Add to active sessions

    @classmethod
    def get_session(cls, session_id):
        """Retrieves an existing session by ID."""
        return cls._sessions.get(session_id)

    def add_message(self, sender, message):
        """Adds a message to the chat history."""
        log_entry = {
            "sender": sender,
            "message": message,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.chat_history.append(log_entry)
        return log_entry # Return for logging to backend

    def reset_session(self):
        """Resets the chat history and context for the current session."""
        self.chat_history = []
        self.context = {
            "last_searched_products": [],
            "last_viewed_product_id": None,
            "current_flow": None,
            "logged_in": False,
            "username": None,
            "session_token": None
        }
        self.add_message("chatbot", "Conversation has been reset. How can I help you start fresh?")

    def update_context(self, key, value):
        """Updates a specific context variable."""
        self.context[key] = value

    def get_context(self, key):
        """Retrieves a specific context variable."""
        return self.context.get(key)