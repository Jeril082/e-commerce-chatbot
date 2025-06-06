# chatbot_logic/api_gateway.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from chatbot import SalesChatbot
from chat_session import ChatSession

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

chatbot = SalesChatbot(ecom_server_url="http://localhost:5000") # Ensure this matches your e-commerce server port

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_query = data.get('query')
    session_id = data.get('session_id')
    user_id = data.get('user_id') # Passed from frontend if logged in

    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    # Retrieve or create session
    session = ChatSession.get_session(session_id)
    if not session:
        session = ChatSession(user_id=user_id if user_id else "guest")
    else:
        # Update session's user_id if it changes (e.g., after login)
        if user_id and session.user_id == "guest":
            session.user_id = user_id
            session.update_context('user_id', user_id)

    # If login happens on frontend, update chatbot's internal session context
    if data.get('logged_in_user_id'):
        session.update_context('logged_in', True)
        session.update_context('user_id', data['logged_in_user_id'])
        session.update_context('username', data['logged_in_username']) # Assuming frontend passes this

    response_data = chatbot.process_query(user_query, session)
    return jsonify(response_data)

@app.route('/session/<session_id>', methods=['GET'])
def get_session_info(session_id):
    session = ChatSession.get_session(session_id)
    if session:
        return jsonify({
            "session_id": session.session_id,
            "user_id": session.user_id,
            "chat_history": session.chat_history,
            "context": session.context,
            "start_time": session.start_time.isoformat()
        })
    return jsonify({"error": "Session not found"}), 404

if __name__ == '__main__':
    print("Running Flask Chatbot API Gateway...")
    app.run(debug=True, port=5001) # Run on a different port than e-commerce server