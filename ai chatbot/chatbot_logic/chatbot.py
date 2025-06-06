# chatbot_logic/chatbot.py

import requests
import json
import re # Import regex for advanced pattern matching
from chat_session import ChatSession # Import our session manager

class SalesChatbot:
    def __init__(self, ecom_server_url="http://localhost:5000"):
        self.ecom_server_url = ecom_server_url

        # Define keywords for different intents
        self.greet_keywords = ["hello", "hi", "hey", "hola"]
        self.goodbye_keywords = ["bye", "goodbye", "exit", "quit", "see ya"]
        self.thank_keywords = ["thank", "thanks", "thank you"]
        self.reset_keywords = ["reset", "start over", "clear chat", "new conversation"]
        self.login_keywords = ["login", "log in", "sign in"]
        self.view_cart_keywords = ["what's in my cart", "view cart", "show my cart", "my cart", "cart"]
        self.checkout_keywords = ["checkout", "place order", "pay now", "buy now"]
        self.product_details_keywords = ["details about", "tell me about", "info on", "describe", "what about"]
        self.add_to_cart_keywords = ["add to cart", "buy", "add this", "put in cart"]
        self.remove_from_cart_keywords = ["remove from cart", "delete from cart", "take out of cart", "remove this"]
        self.product_search_keywords = [
            "search", "find", "look for", "get me", "show me", "browse",
            "show", "list", "display", "products", "items", "available"
        ] # Added more variations for "show products"

    def _extract_price_range(self, query):
        """Extracts min and max price from query using regex."""
        entities = {}
        # Matches "under $XX", "below $XX", "$XX or less"
        max_price_match = re.search(r'(?:under|below|\$?(\d+)\s*or less)', query)
        if max_price_match:
            entities['max_price'] = float(max_price_match.group(1) or (max_price_match.group(2) if max_price_match.group(2) else None)) 
        
        # Matches "over $XX", "above $XX", "$XX or more"
        min_price_match = re.search(r'(?:over|above|\$?(\d+)\s*or more)', query)
        if min_price_match:
            entities['min_price'] = float(min_price_match.group(1) or (min_price_match.group(2) if min_price_match.group(2) else None))
            
        # Matches "$X to $Y" or "$X and $Y"
        range_match = re.search(r'\$?(\d+)\s*(?:to|and)\s*\$?(\d+)', query)
        if range_match:
            entities['min_price'] = float(range_match.group(1))
            entities['max_price'] = float(range_match.group(2))

        return entities

    def _recognize_intent_and_entities(self, query, session):
        """
        A simplified mock NLU (Natural Language Understanding).
        In a real scenario, this would be a sophisticated AI model (e.g., using Rasa, Dialogflow).
        It identifies what the user wants to do (intent) and key information (entities).
        """
        lower_query = query.lower()
        intent = "unknown"
        entities = {}

        # --- High-Priority Intents ---
        if any(kw in lower_query for kw in self.goodbye_keywords):
            intent = "goodbye"
        elif any(kw in lower_query for kw in self.thank_keywords):
            intent = "thank"
        elif any(kw in lower_query for kw in self.reset_keywords):
            intent = "reset_conversation"
        elif any(kw in lower_query for kw in self.greet_keywords):
            intent = "greet"
        elif any(kw in lower_query for kw in self.login_keywords):
            intent = "login"

        # --- Cart/Checkout Intents (more specific than general product search) ---
        elif any(kw in lower_query for kw in self.checkout_keywords):
            intent = "checkout"
        elif any(kw in lower_query for kw in self.view_cart_keywords):
            intent = "view_cart"
        elif any(kw in lower_query for kw in self.remove_from_cart_keywords):
            intent = "remove_from_cart"
            # Extract product name for removal
            for kw in self.remove_from_cart_keywords:
                if kw in lower_query:
                    parts = lower_query.split(kw, 1)
                    if len(parts) > 1:
                        product_name = parts[1].strip().replace("from cart", "").strip()
                        if product_name:
                            entities['product_name'] = product_name
                            break
            # Fallback to last viewed/searched if no name
            if not entities.get('product_name') and session.get_context('last_viewed_product_id'):
                entities['product_id'] = session.get_context('last_viewed_product_id')


        elif any(kw in lower_query for kw in self.add_to_cart_keywords):
            intent = "add_to_cart"
            # Extract product name for adding
            for kw in self.add_to_cart_keywords:
                if kw in lower_query:
                    parts = lower_query.split(kw, 1)
                    if len(parts) > 1:
                        product_name = parts[0].replace("add ", "").strip() if "add " in parts[0] else parts[1].strip()
                        if product_name:
                            entities['product_name'] = product_name
                            break
            # Fallback to last viewed/searched
            if not entities.get('product_name') and session.get_context('last_viewed_product_id'):
                entities['product_id'] = session.get_context('last_viewed_product_id')
            elif not entities.get('product_name') and session.get_context('last_searched_products'):
                # Default to first searched product if no other info
                entities['product_id'] = session.get_context('last_searched_products')[0]['id']


        # --- Product Details (more specific than general search) ---
        elif any(kw in lower_query for kw in self.product_details_keywords):
            intent = "product_details"
            for kw in self.product_details_keywords:
                if kw in lower_query:
                    parts = lower_query.split(kw, 1)
                    if len(parts) > 1:
                        entities['product_name'] = parts[1].strip()
                        break
            # Fallback to last viewed/searched if no name
            if not entities.get('product_name'):
                if session.get_context('last_viewed_product_id'):
                    entities['product_id'] = session.get_context('last_viewed_product_id')
                elif session.get_context('last_searched_products'):
                    entities['product_id'] = session.get_context('last_searched_products')[0]['id'] # First product

        # --- Product Search / Browse (more general) ---
        # This condition is broader and comes after more specific ones
        elif any(kw in lower_query for kw in self.product_search_keywords):
            intent = "search_product"
            # Extract product name
            product_name_patterns = [
                r'search for (.+)', r'look for (.+)', r'find (.+)', r'show me (.+)', r'browse (.+)',
                r'what (?:are|do you have) (?:about|on)? (.+)', r'get me (.+)'
            ]
            for pattern in product_name_patterns:
                match = re.search(pattern, lower_query)
                if match:
                    entities['product_name'] = match.group(1).strip()
                    break
            # If no specific product name, but just general "show products"
            if not entities.get('product_name') and any(kw in lower_query for kw in ["products", "items"]):
                entities['product_name'] = "" # Indicate general product search

            # Basic entity extraction for category/brand
            category_match = re.search(r'category\s*(\w+)', lower_query)
            if category_match:
                entities['category'] = category_match.group(1)
            brand_match = re.search(r'brand\s*(\w+)', lower_query)
            if brand_match:
                entities['brand'] = brand_match.group(1)

            # Price extraction
            entities.update(self._extract_price_range(lower_query))


        return intent, entities

    def _call_ecom_api(self, endpoint, method="GET", data=None, session_id=None):
        """Helper to call the e-commerce server API."""
        url = f"{self.ecom_server_url}/{endpoint}"
        headers = {}
        if session_id:
            # In a real app, this would be a secure token
            headers['X-Session-ID'] = session_id

        try:
            if method == "GET":
                response = requests.get(url, params=data, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with e-commerce server {url}: {e}")
            return {"error": f"Could not connect to the e-commerce service: {e}"}

    def process_query(self, query, session: ChatSession):
        """Processes a user query and returns a chatbot response."""
        # Convert the incoming query to lowercase for consistent checks within this function
        lower_input = query.lower() # THIS IS THE CRUCIAL LINE ADDED/MODIFIED

        intent, entities = self._recognize_intent_and_entities(query, session)
        response_text = "I'm not sure how to help with that. Can you rephrase or ask about products, cart, or checkout?"
        product_display_data = [] # To hold product cards for display in UI

        # Log user message
        session.add_message("user", query)
        self._call_ecom_api("chat_logs", method="POST", data={
            "session_id": session.session_id, "sender": "user", "message": query
        })

        user_id = session.get_context('user_id') # Get current logged in user_id

        # --- Intent Handling ---
        if intent == "greet":
            response_text = "Hello! I'm your shopping assistant. How can I help you today?"
        elif intent == "thank":
            response_text = "You're welcome! Let me know if you need anything else."
        elif intent == "goodbye":
            response_text = "Goodbye! Happy shopping!"
        elif intent == "reset_conversation":
            session.reset_session()
            response_text = "Okay, I've reset our conversation. What would you like to do now?"

        elif intent == "login":
            if session.get_context('logged_in'):
                response_text = f"You are already logged in as {session.get_context('username')}."
            else:
                response_text = "To log in, please use the login form on the page. For this demo, we assume 'testuser' and 'password'."

        elif intent == "search_product":
            product_name = entities.get('product_name', '')
            category = entities.get('category', '')
            brand = entities.get('brand', '')
            min_price = entities.get('min_price')
            max_price = entities.get('max_price')

            search_params = {}
            if product_name: search_params['query'] = product_name # Changed 'q' to 'query' for consistency with backend
            if category: search_params['category'] = category
            if brand: search_params['brand'] = brand
            if min_price is not None: search_params['min_price'] = min_price
            if max_price is not None: search_params['max_price'] = max_price

            # If no specific search term, but general intent to show products
            # This is where the 'lower_query' error occurred in your previous code.
            # It's now corrected to use 'lower_input'.
            if not search_params and (any(kw in lower_input for kw in ["products", "items"])): # Corrected variable name
                response_text = "Here are some general products:"
                data = self._call_ecom_api("products", method="GET") # Get all products if no specific query
            elif not search_params: # If search intent but no entities extracted
                response_text = "What product are you looking for? You can search by name, category, brand, or price range."
                data = None # No search to perform yet
            else: # Perform search with extracted parameters
                data = self._call_ecom_api("products", method="GET", data=search_params)

            if data and not data.get('error'):
                products = data.get('products', [])
                if products:
                    if not product_name and not category and not brand and min_price is None and max_price is None:
                        response_text = "Here are some products from our catalog:" # More general message if no specific query
                    else:
                        response_text = f"Here are some results for {product_name or category or brand or 'your search'}:"
                    product_display_data = products
                    session.update_context('last_searched_products', products)
                    session.update_context('last_viewed_product_id', products[0]['id'] if products else None)
                else:
                    response_text = f"Sorry, I couldn't find any products matching your criteria."
            elif data: # If there was an error from the API call
                response_text = data.get('error', 'An error occurred while searching for products.')


        elif intent == "product_details":
            product_id = entities.get('product_id')
            product_name = entities.get('product_name')

            target_product = None
            if product_id:
                target_product = self._call_ecom_api(f"products/{product_id}")
            elif product_name:
                search_data = self._call_ecom_api("products", method="GET", data={"query": product_name}) # Use 'query'
                if search_data and not search_data.get('error') and search_data.get('products'):
                    target_product = search_data['products'][0] # Take the first match

            if target_product and not target_product.get('error'):
                session.update_context('last_viewed_product_id', target_product['id'])
                response_text = (f"**{target_product['name']}**\n"
                                 f"Description: {target_product['description']}\n"
                                 f"Price: ${target_product['price']:.2f}\n"
                                 f"Category: {target_product['category']}\n"
                                 f"Brand: {target_product['brand']}\n"
                                 f"In Stock: {target_product['stock']} units")
                product_display_data = [target_product] # Display this specific product
            else:
                response_text = f"Sorry, I couldn't find details for that product."

        elif intent == "add_to_cart":
            if not user_id:
                response_text = "Please log in first to add items to your cart."
            else:
                product_id_to_add = entities.get('product_id')
                product_name_from_entities = entities.get('product_name')

                if not product_id_to_add and product_name_from_entities:
                    search_data = self._call_ecom_api("products", method="GET", data={"query": product_name_from_entities}) # Use 'query'
                    if search_data and not search_data.get('error') and search_data.get('products'):
                        product_id_to_add = search_data['products'][0]['id'] # Take the first match

                if product_id_to_add:
                    quantity = 1 # Default quantity
                    add_response = self._call_ecom_api("cart/add", method="POST",
                                                         data={"user_id": user_id, "product_id": product_id_to_add, "quantity": quantity})
                    if add_response and not add_response.get('error'):
                        response_text = f"{add_response['message']}"
                    else:
                        response_text = add_response.get('error', 'Failed to add product to cart.')
                else:
                    response_text = "Which product would you like to add to your cart? Please specify a name or ID."

        elif intent == "remove_from_cart":
            if not user_id:
                response_text = "Please log in first to modify your cart."
            else:
                product_id_to_remove = entities.get('product_id')
                product_name_from_entities = entities.get('product_name')

                if not product_id_to_remove and product_name_from_entities:
                    search_data = self._call_ecom_api("products", method="GET", data={"query": product_name_from_entities}) # Use 'query'
                    if search_data and not search_data.get('error') and search_data.get('products'):
                        product_id_to_remove = search_data['products'][0]['id']

                if product_id_to_remove:
                    remove_response = self._call_ecom_api("cart/remove", method="POST",
                                                             data={"user_id": user_id, "product_id": product_id_to_remove})
                    if remove_response and not remove_response.get('error'):
                        response_text = f"{remove_response['message']}"
                    else:
                        response_text = remove_response.get('error', 'Failed to remove product from cart.')
                else:
                    response_text = "Which product would you like to remove from your cart? Please specify a name or ID."

        elif intent == "view_cart":
            if not user_id:
                response_text = "Please log in first to view your cart."
            else:
                cart_data = self._call_ecom_api(f"cart/{user_id}")
                if cart_data and not cart_data.get('error'):
                    items = cart_data.get('items', [])
                    if items:
                        response_text = "Here's what's in your cart:\n"
                        for item in items:
                            response_text += f"- {item['name']} (x{item['quantity']}) - ${item['price'] * item['quantity']:.2f}\n"
                        response_text += f"Total: ${cart_data['total_price']:.2f}"
                        product_display_data = items # Display cart items as product cards
                    else:
                        response_text = "Your cart is empty."
                else:
                    response_text = cart_data.get('error', 'An error occurred while viewing your cart.')

        elif intent == "checkout":
            if not user_id:
                response_text = "Please log in first to checkout."
            else:
                checkout_response = self._call_ecom_api("checkout", method="POST", data={"user_id": user_id})
                if checkout_response and not checkout_response.get('error'):
                    response_text = (f"Thank you for your purchase! {checkout_response['message']}. "
                                     f"Your Order ID is: {checkout_response['order_id']}. "
                                     f"Total amount: ${checkout_response['total_amount']:.2f}")
                else:
                    response_text = checkout_response.get('error', 'Failed to process checkout. Your cart might be empty or an error occurred.')

        # Log chatbot message
        session.add_message("chatbot", response_text)
        self._call_ecom_api("chat_logs", method="POST", data={
            "session_id": session.session_id, "sender": "chatbot", "message": response_text
        })

        return {"text": response_text, "products": product_display_data, "session_id": session.session_id, "user_id": user_id}