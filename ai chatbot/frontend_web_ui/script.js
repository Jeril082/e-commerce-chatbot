// frontend_web_ui/script.js

const chatHistory = document.getElementById('chat-history');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const resetButton = document.getElementById('reset-button');
const loginToggle = document.getElementById('login-toggle');
const loginStatusSpan = document.getElementById('login-status');

const loginModal = document.getElementById('login-modal');
const closeModalButton = loginModal.querySelector('.close-button');
const performLoginButton = document.getElementById('perform-login');
const loginUsernameInput = document.getElementById('login-username');
const loginPasswordInput = document.getElementById('login-password');
const loginMessage = document.getElementById('login-message');

const CHATBOT_API_URL = 'http://localhost:5001/chat'; // Chatbot API Gateway
const ECOM_API_URL = 'http://localhost:5000'; // E-commerce API (for direct login)

let currentSessionId = localStorage.getItem('chatbotSessionId') || null;
let currentUserId = localStorage.getItem('loggedInUserId') || null;
let currentUsername = localStorage.getItem('loggedInUsername') || null;

// --- Utility Functions ---

function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function appendMessage(sender, text, products = []) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);

    const avatarDiv = document.createElement('div');
    avatarDiv.classList.add('avatar');
    avatarDiv.textContent = sender === 'user' ? '👤' : '🤖';

    const textDiv = document.createElement('div');
    textDiv.classList.add('text');
    // Basic markdown support: bold for **text**
    textDiv.innerHTML = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    const timestampDiv = document.createElement('div');
    timestampDiv.classList.add('timestamp');
    timestampDiv.textContent = formatTimestamp(new Date().toISOString());

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(textDiv);
    messageDiv.appendChild(timestampDiv); // Append timestamp to messageDiv directly

    chatHistory.appendChild(messageDiv);

    // Append product cards if available
    if (products && products.length > 0) {
        products.forEach(product => {
            const productCard = document.createElement('div');
            productCard.classList.add('product-card');
            productCard.innerHTML = `
                <img src="${product.image_url || 'https://via.placeholder.com/150?text=No+Image'}" alt="${product.name}">
                <div class="product-card-details">
                    <h4>${product.name}</h4>
                    <p>${product.description.substring(0, 70)}...</p>
                    <p class="price">Price: $${product.price ? product.price.toFixed(2) : 'N/A'}</p>
                    <button class="add-to-cart-btn" data-product-id="${product.id}" data-product-name="${product.name}">Add to Cart</button>
                </div>
            `;
            chatHistory.appendChild(productCard);
        });
        // Attach event listeners to new Add to Cart buttons
        document.querySelectorAll('.add-to-cart-btn').forEach(button => {
            button.onclick = (e) => {
                const productId = e.target.dataset.productId;
                const productName = e.target.dataset.productName;
                sendMessage(`add ${productName} to cart`, { productId: productId });
            };
        });
    }

    chatHistory.scrollTop = chatHistory.scrollHeight; // Scroll to bottom
}

async function sendMessage(query, additionalData = {}) {
    if (!query.trim() && !additionalData.productId) return; // Don't send empty queries

    appendMessage('user', query); // Display user's message immediately
    userInput.value = ''; // Clear input field

    try {
        const payload = {
            query: query,
            session_id: currentSessionId,
            user_id: currentUserId, // Always send user_id if available
            logged_in_user_id: currentUserId, // Redundant but explicit for chatbot_api
            logged_in_username: currentUsername,
            ...additionalData // For things like product_id from button clicks
        };

        const response = await fetch(CHATBOT_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (data.session_id && !currentSessionId) {
            currentSessionId = data.session_id;
            localStorage.setItem('chatbotSessionId', currentSessionId);
        }
        if (data.user_id && !currentUserId) { // If chatbot returns user_id after login
            currentUserId = data.user_id;
            localStorage.setItem('loggedInUserId', currentUserId);
        }

        appendMessage('chatbot', data.text, data.products);

    } catch (error) {
        console.error('Error sending message to chatbot:', error);
        appendMessage('chatbot', 'Sorry, I am having trouble connecting to my brain right now. Please try again later.');
    }
}

async function handleLogin() {
    const username = loginUsernameInput.value;
    const password = loginPasswordInput.value;
    loginMessage.textContent = ''; // Clear previous messages

    try {
        const response = await fetch(`${ECOM_API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });
        const data = await response.json();

        if (response.ok) {
            currentUserId = data.user_id;
            currentUsername = username;
            localStorage.setItem('loggedInUserId', currentUserId);
            localStorage.setItem('loggedInUsername', currentUsername);
            localStorage.setItem('sessionToken', data.session_id); // This is mock token

            updateLoginStatus();
            loginModal.style.display = 'none'; // Hide modal
            appendMessage('chatbot', `Hello ${currentUsername}! You are now logged in. How can I help you today?`);

            // Also send a message to the chatbot API to update its session context
            await fetch(CHATBOT_API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: "user logged in", // Inform chatbot of login
                    session_id: currentSessionId,
                    user_id: currentUserId,
                    logged_in_user_id: currentUserId,
                    logged_in_username: currentUsername
                })
            });

        } else {
            loginMessage.textContent = data.error || 'Login failed. Please check your credentials.';
        }
    } catch (error) {
        console.error('Login API error:', error);
        loginMessage.textContent = 'Could not connect to login service.';
    }
}

function updateLoginStatus() {
    if (currentUserId && currentUsername) {
        loginStatusSpan.textContent = `Logged In as ${currentUsername}`;
        loginToggle.textContent = 'Logout';
        loginToggle.classList.remove('login-btn');
        loginToggle.classList.add('logout-btn'); // Add a specific class for logout styling if desired
    } else {
        loginStatusSpan.textContent = 'Not Logged In';
        loginToggle.textContent = 'Login';
        loginToggle.classList.add('login-btn');
        loginToggle.classList.remove('logout-btn');
    }
}

function handleLogout() {
    currentUserId = null;
    currentUsername = null;
    localStorage.removeItem('loggedInUserId');
    localStorage.removeItem('loggedInUsername');
    localStorage.removeItem('sessionToken'); // Clear mock token
    updateLoginStatus();
    appendMessage('chatbot', 'You have been logged out.');
}

// --- Event Listeners ---
sendButton.addEventListener('click', () => sendMessage(userInput.value));
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage(userInput.value);
    }
});

resetButton.addEventListener('click', () => {
    localStorage.removeItem('chatbotSessionId'); // Clear session from local storage
    currentSessionId = null; // Reset current session variable
    chatHistory.innerHTML = ''; // Clear chat history from display
    appendMessage('chatbot', "Conversation has been reset. How can I help you start fresh?");
    sendMessage("reset_conversation"); // Inform backend to reset session logic too
});

loginToggle.addEventListener('click', () => {
    if (currentUserId) {
        handleLogout();
    } else {
        loginModal.style.display = 'flex'; // Show modal
        loginMessage.textContent = ''; // Clear messages on open
        loginUsernameInput.value = 'testuser'; // Pre-fill for demo
        loginPasswordInput.value = 'password'; // Pre-fill for demo
    }
});

closeModalButton.addEventListener('click', () => {
    loginModal.style.display = 'none'; // Hide modal
});

performLoginButton.addEventListener('click', handleLogin);

// Close modal if user clicks outside of it
window.addEventListener('click', (event) => {
    if (event.target === loginModal) {
        loginModal.style.display = 'none';
    }
});

// Initialize login status on page load
updateLoginStatus();
// Restore chat history if session exists (requires fetching from chatbot_api /session/<id>)
// For simplicity in this demo, we won't restore history on refresh, only session_id
// If you implement fetching history, you'd call chatbot_api/session/<id> and populate appendMessage