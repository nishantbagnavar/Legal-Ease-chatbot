import streamlit as st
import os
from dotenv import load_dotenv

# Import constants
from constants import USERS_FILE, CHAT_HISTORY_DIR, STYLES

# Import utility functions
from utils import initialize_session_state, logout

# Import page rendering functions
from pages import introduction_page, login_page, signup_page, chatbot_page

# Load environment variables (ensure .env file exists with GROQ_API_KEY)
load_dotenv()

# --- Configuration & Setup ---

# Ensure chat history directory exists
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

# Streamlit UI Setup
st.set_page_config(page_title="LegalEase AI", layout="wide")

# Apply custom CSS
st.markdown(STYLES, unsafe_allow_html=True)

# Initialize session state variables
initialize_session_state()

# --- Main Application Logic ---

# Check if the user is logged in
if not st.session_state.logged_in:
    # If not logged in, display authentication pages
    if st.session_state.page == "introduction":
        introduction_page()
    elif st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":
        signup_page()
else:
    # If logged in, display the chatbot page
    chatbot_page()

# Streamlit requires a way to exit or rerun.
# In a multi-page setup like this, the page functions handle st.rerun() directly.
# This ensures the app flow is managed by session_state.page changes.
