# --- Configuration Constants ---
USERS_FILE = "users.json"
CHAT_HISTORY_DIR = "chat_histories"

# --- Global CSS Styles (Adapted for Dark Theme) ---
STYLES = """
<style>
    body {
        font-family: 'Inter', sans-serif;
        background-color: #1A202C; /* Dark background */
        color: #E2E8F0; /* Light text color */
    }
    h1, h2 {
        color: #63B3ED; /* Lighter blue for headers */
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    h1 {
        text-align: center;
        margin-bottom: 20px;
    }
    h2 {
        margin-top: 30px;
        margin-bottom: 15px;
        border-bottom: 1px solid #4A5568; /* Darker, subtle border */
        padding-bottom: 5px;
    }
    .stContainer {
        border-radius: 12px;
        padding: 30px;
        background-color: #2D3748; /* Darker container background */
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4); /* More prominent shadow for dark theme */
        margin-bottom: 20px;
    }
    .stButton>button {
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        background-color: #4299E1; /* Primary button color */
        color: white; /* White text on primary button */
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        background-color: #3182CE; /* Slightly darker hover */
    }
    .stChatMessage {
        border-radius: 18px !important;
        padding: 12px 16px !important;
        margin-bottom: 12px !important;
        max-width: 85% !important;
        word-wrap: break-word !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
    }
    [data-testid="chat-message-user"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; /* Keep a vibrant user message */
        color: white !important;
        margin-left: auto !important;
        margin-right: 8px !important;
    }
    [data-testid="chat-message-assistant"] {
        background: #2A4365 !important; /* Darker background for assistant messages */
        border: 1px solid #4A5568 !important; /* Darker border */
        color: #E2E8F0 !important; /* Light text for assistant messages */
        margin-right: auto !important;
        margin-left: 8px !important;
    }
    .stChatInputContainer {
        border-top: 1px solid #4A5568; /* Darker border for input */
        padding-top: 1rem;
        background: #2D3748; /* Darker input background */
    }
    .source-citation {
        font-size: 0.85em;
        color: #A0AEC0; /* Lighter grey for citation text */
        margin-top: 8px;
        padding: 8px 12px;
        background: #2D3748; /* Darker background for citation box */
        border-left: 3px solid #63B3ED; /* Lighter blue for citation border */
        border-radius: 4px;
    }
    .source-citation strong {
        color: #90CDF4; /* Even lighter blue for strong text in citation */
    }
    .chat-container {
        height: 500px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #4A5568; /* Darker border */
        border-radius: 12px;
        background: #2D3748; /* Darker background for chat container */
        margin-bottom: 1rem;
    }
    .feature-list {
        list-style-type: none;
        padding: 0;
        text-align: left;
        display: inline-block; /* To center the list itself */
        margin-bottom: 20px;
    }
    .feature-list li {
        margin-bottom: 10px;
        font-size: 1.1em;
        color: #A0AEC0; /* Lighter text for features */
    }
    .feature-list li::before {
        content: '✓';
        color: #63B3ED; /* Lighter blue checkmark color */
        font-weight: bold;
        display: inline-block;
        width: 1em;
        margin-left: -1em;
    }
</style>
"""
