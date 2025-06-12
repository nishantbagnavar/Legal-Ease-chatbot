import streamlit as st
import os
import json
import time # Imported for potential future use or if needed by perform_web_search later
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory, HumanMessage, AIMessage # Import both classes

# Import constants
from constants import USERS_FILE, CHAT_HISTORY_DIR

# Fixed import for Google Search, moved here as perform_web_search is in this file
try:
    from googlesearch import search as google_search
    GOOGLE_SEARCH_AVAILABLE = True
except ImportError:
    GOOGLE_SEARCH_AVAILABLE = False
    # No st.warning here, as it's a utility file. warnings will be in pages.py

# --- User Management Functions ---
def load_users():
    """Loads user data from the users.json file."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Handle empty or corrupted file
            return {}
    return {}

def save_users(users_data):
    """Saves user data to the users.json file."""
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users_data, f, indent=4)
    except Exception as e:
        st.error(f"Error saving user data: {e}")

def add_user(username, password):
    """Adds a new user to the system."""
    if not username or not password:
        return False, "Username and password cannot be empty."
    
    users = load_users()
    if username in users:
        return False, "Username already exists."
    
    users[username] = password
    save_users(users)
    return True, "Account created successfully. You can now log in."

def verify_user(username, password):
    """Verifies user credentials."""
    users = load_users()
    return username in users and users[username] == password

# --- Chat History Management Functions ---
def get_chat_history_file_path(username, session_id):
    """Generates the file path for a user's chat history."""
    user_dir = os.path.join(CHAT_HISTORY_DIR, username)
    os.makedirs(user_dir, exist_ok=True) # Ensure user directory exists
    return os.path.join(user_dir, f"{session_id}.json")

def load_user_chat_history(username, session_id):
    """Loads chat history for a given user and session."""
    file_path = get_chat_history_file_path(username, session_id)
    chat_history = ChatMessageHistory()
    messages = []
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                raw_messages = json.load(f)
                for msg_data in raw_messages:
                    messages.append({"role": msg_data["type"], "content": msg_data["content"]})
                    # Reconstruct ChatMessageHistory
                    if msg_data["type"] == "human":
                        chat_history.add_user_message(msg_data["content"])
                    elif msg_data["type"] == "ai":
                        chat_history.add_ai_message(msg_data["content"])
        except (json.JSONDecodeError, FileNotFoundError) as e:
            # Handle case where file is empty or corrupted, log to console
            print(f"Warning: Could not load chat history for session '{session_id}': {e}")
    
    return chat_history, messages

def save_user_chat_history(username, session_id, chat_history: BaseChatMessageHistory):
    """Saves chat history for a given user and session."""
    try:
        file_path = get_chat_history_file_path(username, session_id)
        # Convert messages to a serializable format (list of dicts)
        serializable_messages = [{"type": msg.type, "content": msg.content} for msg in chat_history.messages]
        with open(file_path, "w") as f:
            json.dump(serializable_messages, f, indent=4)
    except Exception as e:
        st.error(f"Error saving chat history: {e}")

def get_session_history_wrapper(session_id: str) -> BaseChatMessageHistory:
    """Wrapper function to get or create chat history for RunnableWithMessageHistory."""
    # Ensure username is available in session state
    if st.session_state.username is None:
        return ChatMessageHistory() # Return an empty history if no user is logged in
    
    # Load history only once per session_id
    if session_id not in st.session_state.store:
        st.session_state.store[session_id], _ = load_user_chat_history(st.session_state.username, session_id)
    return st.session_state.store[session_id]

def clear_chat_history(session_id):
    """Clears chat history for a specific session for the current user."""
    if f"messages_{session_id}" in st.session_state:
        del st.session_state[f"messages_{session_id}"]
    
    if session_id in st.session_state.store:
        del st.session_state.store[session_id]
    
    # Also delete the physical file
    history_file = get_chat_history_file_path(st.session_state.username, session_id)
    if os.path.exists(history_file):
        os.remove(history_file)
    
    st.success(f"Chat history for session '{session_id}' cleared.")
    st.rerun()

def logout():
    """Logs out the user and resets relevant session state variables."""
    keys_to_reset = [
        "logged_in", "username", "api_key", "store", "uploaded_doc_names", 
        "selected_language", "vectorstore", "full_document_content", "document_chunks"
    ]
    
    for key in keys_to_reset:
        if key in st.session_state:
            if key == "logged_in":
                st.session_state[key] = False
            elif key in ["username", "api_key"]:
                st.session_state[key] = ""
            elif key in ["store", "uploaded_doc_names"]:
                # Ensure correct default type (list for uploaded_doc_names, dict for store)
                st.session_state[key] = [] if key == "uploaded_doc_names" else {}
            elif key == "selected_language":
                st.session_state[key] = "English" # Default language
            else:
                del st.session_state[key] # Delete other specific keys
    
    # Clear message history for all sessions from session state
    keys_to_delete = [key for key in st.session_state.keys() if key.startswith("messages_")]
    for key in keys_to_delete:
        del st.session_state[key]
    
    st.cache_resource.clear() # Clear Streamlit's resource cache
    st.session_state.page = "introduction" # Redirect to intro page

# --- Session State Initialization ---
def initialize_session_state():
    """Initializes default values for Streamlit session state variables."""
    defaults = {
        "logged_in": False,
        "username": None,
        "store": {}, # Used to store ChatMessageHistory objects
        "api_key": "",
        "page": "introduction", # Controls which page is displayed
        "uploaded_doc_names": [], # Names of documents uploaded by user
        "messages": [], # Current session messages (used by chat_message)
        "selected_language": "English",
        "vectorstore": None, # Stores FAISS vector store
        "full_document_content": "", # Raw text content of uploaded documents
        "document_chunks": [], # List of Document objects from text splitting
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- Web Search Function ---
def perform_web_search(query):
    """Performs a web search using the googlesearch library."""
    global GOOGLE_SEARCH_AVAILABLE # Ensure we use the global variable
    if not GOOGLE_SEARCH_AVAILABLE:
        # st.warning("Google search functionality not available. Please install 'googlesearch-python'.")
        return {} # Return empty if functionality is not available
    
    try:
        # num_results=3 for reasonable performance and breadth
        search_results = list(google_search(query, num_results=3, lang='en'))
        if search_results:
            # Return the first result as a representative snippet
            return {
                "title": "Web Search Results", # Placeholder title
                "snippet": f"Found {len(search_results)} results for your query. Top result: {search_results[0]}",
                "url": search_results[0] if search_results else "#" # Link to the top result
            }
        else:
            return {} # No results found
    except Exception as e:
        # Log error to console for debugging, don't use st.error in utility
        print(f"Error during web search: {e}")
        return {}
