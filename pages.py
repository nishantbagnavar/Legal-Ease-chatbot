import streamlit as st
import time
from deep_translator import GoogleTranslator

# Langchain related imports
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains import create_history_aware_retriever
from langchain_core.runnables import RunnableWithMessageHistory

# Import utility functions from the utils module
from utils import (
    add_user, verify_user, clear_chat_history, logout,
    load_user_chat_history, get_session_history_wrapper, perform_web_search,
    save_user_chat_history, # Added this import
    GOOGLE_SEARCH_AVAILABLE # Import the global variable to check search availability
)

# Import document processing functions from the document_processor module
from document_processor import process_files_and_create_vectorstore


# --- Page Rendering Functions ---
def introduction_page():
    """Renders the introduction page of the application."""
    st.markdown("<h1>⚖ Welcome to LegalEase</h1>", unsafe_allow_html=True)
    
    # Removed the image display for introduction page
    # st.columns and st.image calls are removed.
    
    st.markdown("<p style='text-align: center; color: #666; font-size: 1.1em;'>Your AI-powered assistant for analyzing legal documents with ease.</p>", unsafe_allow_html=True)
    
    st.markdown("---") # Separator

    # Use columns to center the main content box
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("""
            <div style='text-align: center;'>
                <p style='font-size: 1.2em; font-weight: bold; color: #005f73;'>Hello! I am your LegalEase assistant.</p>
                <p>Designed to help you quickly understand complex legal texts and streamline your legal research.</p>
                <h3 style='color: #005f73; margin-top: 25px;'>Key Features:</h3>
                <ul class="feature-list">
                    <li>Answer questions based on your uploaded documents (PDF, DOCX, etc.).</li>
                    <li>Summarize key sections of your documents for quick insights.</li>
                    <li>Extract key entities like parties, dates, and legal terms.</li>
                    <li>Help you find specific information within large documents efficiently.</li>
                    <li>Support multiple languages for clear and accessible responses.</li>
                    <li>Provide fallback answers from Web Search for general legal queries.</li>
                </ul>
                <p style='margin-top: 20px;'>To get started, please log in or create an account.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True) # Spacer for visual separation

            login_col, signup_col = st.columns(2)
            with login_col:
                if st.button("Log In", use_container_width=True, type="primary"):
                    st.session_state.page = "login"
                    st.rerun() # Rerun to switch to the login page
            with signup_col:
                if st.button("Create New Account", use_container_width=True):
                    st.session_state.page = "signup"
                    st.rerun() # Rerun to switch to the signup page

def login_page():
    """Renders the login page of the application."""
    st.markdown("<h1>🔐 Login to LegalEase</h1>", unsafe_allow_html=True)
    
    # Removed the image display for login page
    # st.columns and st.image calls are removed.
    
    st.markdown("<p style='font-size: 1.1em; color: #555; text-align: center;'>Enter your credentials to access your LegalEase AI workspace.</p>", unsafe_allow_html=True)
    
    # Use columns to center the login form
    col_empty, col_form, col_empty2 = st.columns([1, 2, 1])
    with col_form:
        with st.container(border=True):
            st.markdown("<h3>Account Access</h3>", unsafe_allow_html=True)
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            st.session_state.api_key = st.text_input("🔑 Groq API Key (Required)", type="password", key="login_api_key")
            st.warning("A Groq API key is required for the chatbot functionality.")

            st.markdown("<br>", unsafe_allow_html=True) # Spacer
            login_col, signup_col = st.columns(2)
            with login_col:
                if st.button("Login", type="primary", use_container_width=True):
                    if not username or not password:
                        st.error("Please enter both username and password.")
                    elif verify_user(username, password):
                        st.session_state["logged_in"] = True
                        st.session_state.username = username
                        st.session_state.page = "chatbot"
                        st.rerun() # Rerun to switch to the chatbot page
                    else:
                        st.error("Invalid username or password.")
            with signup_col:
                if st.button("Create Account Instead", key="go_to_signup", use_container_width=True):
                    st.session_state.page = "signup"
                    st.rerun() # Rerun to switch to the signup page
            st.markdown("<br>", unsafe_allow_html=True) # Spacer
            st.info("New user? Create an account easily or use a demo account if available.")

def signup_page():
    """Renders the signup page of the application."""
    st.markdown("<h1>✍ Create Your LegalEase Account</h1>", unsafe_allow_html=True)
    
    # Use columns to center the signup form
    col_empty, col_form, col_empty2 = st.columns([1, 2, 1])
    with col_form:
        with st.container(border=True):
            new_username = st.text_input("New Username", key="signup_username")
            new_password = st.text_input("New Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")

            reg_col, back_col = st.columns(2)
            with reg_col:
                if st.button("Register", type="primary", use_container_width=True):
                    if not new_username or not new_password or not confirm_password:
                        st.error("Please fill in all fields.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        success, message = add_user(new_username, new_password)
                        if success:
                            st.success(message)
                            st.session_state.page = "login" # Redirect to login after successful signup
                            st.rerun()
                        else:
                            st.error(message)
            with back_col:
                if st.button("Back to Login", key="back_to_login", use_container_width=True):
                    st.session_state.page = "login"
                    st.rerun() # Redirect to login page

def chatbot_page():
    """Renders the main chatbot interface."""
    st.markdown("<h1>🤖 LegalEase Chatbot</h1>", unsafe_allow_html=True)
    
    api_key = st.session_state.api_key
    llm = None
    
    # Check for API key and initialize LLM
    if not api_key:
        st.error("⚠ Groq API Key is missing. Please go to Login page to provide it.")
    else:
        try:
            llm = ChatGroq(groq_api_key=api_key, model="gemma2-9b-it", temperature=0.2)
        except Exception as e:
            st.error(f"Failed to initialize Groq LLM. Check your Groq API Key: {e}")
            llm = None

    # Sidebar for settings and document upload
    with st.sidebar:
        st.header("Settings")
        st.markdown(f"Logged in as: *{st.session_state.username}*")
        
        if st.button("Logout", use_container_width=True):
            logout() # Calls the logout function from utils.py
            st.rerun()
        
        st.write("---")
        st.header("🌐 Response Language")
        languages = ["English", "Spanish", "French", "German", "Chinese", "Japanese", "Korean", "Arabic", "Russian", "Portuguese", "Italian", "Hindi", "Bengali", "Tamil", "Telugu"]
        st.session_state.selected_language = st.selectbox("Select Response Language", languages, index=0)

        st.write("---")
        st.header("📄 Document Upload")
        uploaded_files = st.file_uploader(
            "Choose files (PDF, DOCX, TXT, etc.)", 
            type=["pdf", "docx", "txt", "pptx", "xls", "xlsx", "csv", "html", "py"], 
            accept_multiple_files=True, 
            key="file_uploader"
        )
        
        if uploaded_files and len(uploaded_files) > 0 and st.button("Process Documents", use_container_width=True):
            st.session_state.vectorstore = process_files_and_create_vectorstore(uploaded_files)
            if st.session_state.vectorstore:
                st.success(f"✅ Knowledge base built from {len(st.session_state.uploaded_doc_names)} document(s).")
                st.rerun() # Rerun to refresh the page after document processing

        if st.session_state.uploaded_doc_names:
            st.markdown("### Loaded Documents:")
            for doc_name in st.session_state.uploaded_doc_names:
                st.markdown(f"- {doc_name}")
            
        st.write("---")
        session_id = st.text_input("🆔 Session ID:", value="default_session", key="current_session_id", help="Use different IDs for separate conversations.")
        
        if st.button("🗑 Clear Chat History", key="clear_chat_button", use_container_width=True):
            clear_chat_history(session_id) # Calls the clear_chat_history function from utils.py

    vectorstore = st.session_state.get("vectorstore", None)

    # Main chat interface logic
    if llm:
        # Load messages for the current session ID
        if f"messages_{session_id}" not in st.session_state:
            # The actual chat history for LangChain is handled by get_session_history_wrapper
            # This 'messages' list is purely for displaying in Streamlit's chat_message UI
            _, messages = load_user_chat_history(st.session_state.username, session_id)
            st.session_state[f"messages_{session_id}"] = messages

        st.markdown("<h2>💬 Chat Session</h2>", unsafe_allow_html=True)
        
        with st.container():
            # Display existing messages
            for message in st.session_state[f"messages_{session_id}"]:
                role = "user" if message["role"] == "human" else "assistant"
                avatar = "👤" if role == "user" else "🤖"
                
                with st.chat_message(role, avatar=avatar):
                    st.markdown(message["content"])

        # Handle user input
        if prompt := st.chat_input("💬 Ask a question about your documents or a general legal query..."):
            st.session_state[f"messages_{session_id}"].append({"role": "human", "content": prompt})
            
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="🤖"):
                message_placeholder = st.empty()
                full_response = "⚠ *Gentle reminder: We generally ensure precise information, but do double-check.* \n\n"
                
                rag_succeeded = False
                show_google_search = False
                
                try:
                    if vectorstore:
                        # RAG chain setup
                        retriever = vectorstore.as_retriever()
                        
                        # Contextualize question prompt
                        contextualize_q_prompt = ChatPromptTemplate.from_messages([
                            ("system", "Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question which can be understood without the chat history. Do NOT answer the question, just reformulate it if needed and otherwise return it as is."),
                            MessagesPlaceholder("chat_history"),
                            ("human", "{input}"),
                        ])
                        history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
                        
                        # RAG prompt
                        system_prompt = """
                        You are a knowledge-based AI assistant specializing in providing comprehensive and accurate answers based solely on the provided context. Follow these guidelines:

                        1. Strictly adhere to the provided context: Do not use any outside knowledge. If the answer isn't in the context, state "I don't have enough information to answer that based on the provided documents."
                        2. Provide detailed and exhaustive answers: When the context permits, elaborate on the topic, explaining concepts thoroughly and providing relevant specifics.
                        3. Structure your responses clearly: Use headings, bullet points, or numbered lists when appropriate to make the information easy to read and understand.
                        4. Maintain accuracy and logical coherence: Ensure all parts of your answer are factually correct according to the context and flow logically.
                        5. Prioritize answering the user's direct question: While being detailed, ensure the core of your response directly addresses the user's query.

                        Context:
                        {context}
                        """
                        
                        qa_prompt = ChatPromptTemplate.from_messages([
                            ("system", system_prompt),
                            MessagesPlaceholder("chat_history"),
                            ("human", "{input}"),
                        ])
                        
                        combine_docs_chain = create_stuff_documents_chain(llm, qa_prompt)
                        rag_chain = create_retrieval_chain(history_aware_retriever, combine_docs_chain)

                        # Runnable with message history
                        conversational_rag_chain = RunnableWithMessageHistory(
                            rag_chain,
                            get_session_history_wrapper, # Function to load/get history
                            input_messages_key="input",
                            history_messages_key="chat_history",
                        )
                        
                        with st.spinner("🤔 Searching documents..."):
                            response = conversational_rag_chain.invoke(
                                {"input": prompt},
                                config={"configurable": {"session_id": session_id}} # Pass session ID for history
                            )
                        
                        response_text = response["answer"]
                        
                        # Check if RAG indicates no info from documents (fallback triggers)
                        rag_fallback_triggers = [
                            "not in the document", "does not contain", "no relevant information",
                            "i don't have enough information", "cannot answer that", "i do not have the required data"
                        ]

                        # Decide whether to show Google Search based on RAG response
                        if any(phrase in response_text.lower() for phrase in rag_fallback_triggers) or len(response_text.strip()) < 30:
                            show_google_search = True
                        else:
                            # RAG succeeded, display the response character by character
                            for chunk in response_text.split(" "):
                                full_response += chunk + " "
                                message_placeholder.markdown(full_response + "▌")
                                time.sleep(0.02) # Simulate typing
                            message_placeholder.markdown(full_response)
                            rag_succeeded = True

                            # Handle translation if a language other than English is selected
                            if st.session_state.selected_language != "English":
                                try:
                                    translator = GoogleTranslator(source='auto', target=st.session_state.selected_language.lower())
                                    # Remove initial disclaimer before translation to avoid translating it
                                    translated_response = translator.translate(full_response.replace("⚠ *Gentle reminder: We generally ensure precise information, but do double-check.* \n\n", "").strip())
                                    translated_response_with_disclaimer = "⚠ *Gentle reminder: We generally ensure precise information, but do double-check.* \n\n" + translated_response
                                    message_placeholder.markdown(translated_response_with_disclaimer)
                                    final_response_to_save = translated_response_with_disclaimer
                                except Exception as translate_e:
                                    st.warning(f"Failed to translate to {st.session_state.selected_language}: {translate_e}. Displaying in English.")
                                    final_response_to_save = full_response
                            else:
                                final_response_to_save = full_response

                            # Save the final response (English or translated) to session state and file
                            st.session_state[f"messages_{session_id}"].append({"role": "ai", "content": final_response_to_save})
                            save_user_chat_history(st.session_state.username, session_id, get_session_history_wrapper(session_id))
                            
                            # Display sources if available
                            if "context" in response and response["context"]:
                                sources = set()
                                for doc in response["context"]:
                                    if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                                        sources.add(doc.metadata['source'])
                                
                                if sources:
                                    st.markdown(
                                        f'<div class="source-citation"><strong>Sources:</strong> {", ".join(sources)}</div>',
                                        unsafe_allow_html=True
                                    )
                    else:
                        # If no vectorstore is available, directly fall back to Google Search
                        show_google_search = True

                except Exception as e:
                    # Catch any other errors during RAG and fall back to Google Search
                    st.error(f"Error in RAG processing: {e}")
                    show_google_search = True

                # Handle web search fallback if RAG didn't succeed or failed
                if show_google_search and not rag_succeeded:
                    if not GOOGLE_SEARCH_AVAILABLE:
                        st.warning("Google search functionality is not available. Please install 'googlesearch-python' package.")
                        error_msg = "Sorry, I couldn't find an answer in documents and web search is not available. Please try rephrasing or uploading more documents."
                        message_placeholder.markdown(error_msg)
                        st.session_state[f"messages_{session_id}"].append({"role": "ai", "content": error_msg})
                    else:
                        with st.spinner("🌐 Searching the web..."):
                            web_search_results = perform_web_search(prompt)

                        if web_search_results:
                            title = web_search_results.get("title", "No Title")
                            snippet = web_search_results.get("snippet", "No snippet available.")
                            url = web_search_results.get("url", "#")
                            
                            fallback_answer_base = f"""
🌐 No document context matched your query, but here's something from the web:

*Title:* {title}  
*Snippet:* {snippet}  
[🔗 View Full Article]({url})
                            """
                            
                            # Translate fallback answer if needed
                            if st.session_state.selected_language != "English":
                                try:
                                    translator = GoogleTranslator(source='auto', target=st.session_state.selected_language.lower())
                                    translated_fallback = translator.translate(fallback_answer_base)
                                    final_fallback_answer = translated_fallback
                                except Exception as translate_e:
                                    st.warning(f"Failed to translate web search fallback to {st.session_state.selected_language}: {translate_e}. Displaying in English.")
                                    final_fallback_answer = fallback_answer_base
                            else:
                                final_fallback_answer = fallback_answer_base

                            message_placeholder.markdown(final_fallback_answer)
                            st.session_state[f"messages_{session_id}"].append({"role": "ai", "content": final_fallback_answer})
                        else:
                            error_msg = "Sorry, I couldn't find an answer in documents or via web search. Please try rephrasing or uploading more documents."
                            message_placeholder.markdown(error_msg)
                            st.session_state[f"messages_{session_id}"].append({"role": "ai", "content": error_msg})

                    # Save the web search response to chat history
                    save_user_chat_history(st.session_state.username, session_id, get_session_history_wrapper(session_id))

    else:
        # Message displayed when LLM is not initialized (e.g., missing API key)
        st.error("❗ LLM not initialized. Ensure your Groq API key is provided.")
        st.info("👆 Please upload documents (PDF, DOCX, etc.) in the sidebar and click 'Process Documents' to begin chatting.")

        st.markdown("""
        ### How to get started:
        1. Upload one or more documents using the file uploader in the sidebar.
        2. Click the "Process Documents" button.
        3. Wait for the documents to be processed.
        4. Select your preferred response language.
        5. Start asking questions about your documents in the chat.
        
        ### Example questions you can ask:
        - "What are the main points in this document?"
        - "Can you summarize the key legal terms mentioned?"
        - "What is the concept of 'res judicata'?"
        """)
