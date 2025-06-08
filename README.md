# E-commerce Chatbot

This is a simple yet functional AI-powered chatbot designed to assist users with their shopping experience on an e-commerce platform. It can answer product-related queries, help with cart management, and guide users through the checkout process.

The chatbot interacts with a backend e-commerce API (which is assumed to be running separately, likely from the `ecom_server_project` you might have).

## Features

* **Greetings & Farewell:** Handles basic conversational greetings and goodbyes.
* **Product Search:** Search for products by name, category, brand, or price range.
* **Product Details:** Get detailed information about specific products.
* **Cart Management:** Add items to the cart, remove items from the cart, and view cart contents.
* **Checkout:** Simulate a checkout process for logged-in users.
* **User Login Simulation:** Basic handling for user login context.
* **Conversation Reset:** Allows users to clear the current conversation context.
* **Chat Logging:** Logs user and chatbot messages to the e-commerce backend.

## Project Structure

This project primarily focuses on the chatbot's logic. It assumes the existence of a separate e-commerce backend API.

ecom_chatbot_project/
├── chatbot_logic/
│   ├── chatbot.py           # Core chatbot logic (intent recognition, entity extraction, API calls)
│   └── chat_session.py      # Manages individual user chat sessions and context
├── api_gateway.py           # Flask API Gateway for the chatbot (exposes /chat endpoint)
└── requirements.txt         # Python dependencies

## Prerequisites

Before you begin, ensure you have the following installed:

* **Python 3.8+**
* **An E-commerce Backend API:** This chatbot relies on a separate e-commerce API (e.g., `ecom_server_project`) running at `http://localhost:5000`. Make sure that project is set up and running first.

## Installation

Follow these steps to set up and run the chatbot:

1.  **Clone the Repository (if applicable):**
    If this code is part of a larger repository, clone it first:
    ```bash
    git clone <your-repository-url>
    cd ecom_chatbot_project
    ```
    If you just have the files, navigate to the `ecom_chatbot_project` directory.

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    * **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    * **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Chatbot

To run the chatbot, you need to start its API Gateway.

1.  **Ensure E-commerce Backend is Running:**
    Make sure your e-commerce server (e.g., `ecom_server_project/server.py`) is running, typically on `http://localhost:5000`. The chatbot communicates with this server.

2.  **Start the Chatbot API Gateway:**
    From the `ecom_chatbot_project` directory, run:
    ```bash
    python api_gateway.py
    ```
    You should see output similar to:
    ```
     * Serving Flask app 'api_gateway'
     * Debug mode: on
     WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
     * Running on [http://127.0.0.1:5001](http://127.0.0.1:5001)
     Press CTRL+C to quit
     * Restarting with stat
     * Debugger is active!
     * Debugger PIN: ...
    ```
    The chatbot API will be accessible at `http://127.0.0.1:5001`.

## How to Interact with the Chatbot

You can interact with the chatbot by sending POST requests to its `/chat` endpoint. In a real-world scenario, this would be done by a frontend web application.

Here's an example of how you can test it using `curl` or Postman:

**Example using `curl` (from a new terminal):**

```bash
# Greet the chatbot
curl -X POST -H "Content-Type: application/json" -d '{"session_id": "user123", "message": "Hi there"}' [http://127.0.0.1:5001/chat](http://127.0.0.1:5001/chat)

# Search for products
curl -X POST -H "Content-Type: application/json" -d '{"session_id": "user123", "message": "Show me some laptops"}' [http://127.0.0.1:5001/chat](http://127.0.0.1:5001/chat)

# Get details about a specific product (assuming "Laptop Pro" was in the previous search results)
curl -X POST -H "Content-Type: application/json" -d '{"session_id": "user123", "message": "Details about Laptop Pro"}' [http://127.0.0.1:5001/chat](http://127.0.0.1:5001/chat)

# Add to cart (you need to have a user logged in, which is simulated in your session)
# For this demo, let's assume session_id 'test_session_1' is logged in as 'testuser'
curl -X POST -H "Content-Type: application/json" -d '{"session_id": "test_session_1", "message": "Add Laptop Pro to cart"}' [http://127.0.0.1:5001/chat](http://127.0.0.1:5001/chat)

# View cart
curl -X POST -H "Content-Type: application/json" -d '{"session_id": "test_session_1", "message": "View my cart"}' [http://127.0.0.1:5001/chat](http://127.0.0.1:5001/chat)

# Checkout
curl -X POST -H "Content-Type: application/json" -d '{"session_id": "test_session_1", "message": "Checkout"}' [http://127.0.0.1:5001/chat](http://127.0.0.1:5001/chat)




## 👨‍💻 Author

Jeril Joseph
Cybersecurity & AI Enthusiast

