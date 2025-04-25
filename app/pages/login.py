import streamlit as st
import sqlite3
import hashlib
import time

def show_login():
    st.markdown('<div class="main-header">Login to Your Account</div>', unsafe_allow_html=True)
    
    # Create a centered login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        # Login form
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        # Error message placeholder
        error_placeholder = st.empty()
        
        # Login button
        if st.button("Login", key="login_button"):
            if username and password:
                # Hash the password
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                
                # Check credentials in database
                conn = sqlite3.connect('database/stock_analyzer.db')
                c = conn.cursor()
                c.execute("SELECT id, username FROM users WHERE username = ? AND password = ?", (username, hashed_password))
                user = c.fetchone()
                conn.close()
                
                if user:
                    # Set session state
                    st.session_state.user_id = user[0]
                    st.session_state.username = user[1]
                    
                    # Show success message and redirect
                    st.success("Login successful! Redirecting...")
                    time.sleep(1)
                    st.rerun()
                else:
                    error_placeholder.error("Invalid username or password. Please try again.")
            else:
                error_placeholder.error("Please enter both username and password.")
        
        st.markdown('<div class="divider">OR</div>', unsafe_allow_html=True)
        
        # Demo account login
        if st.button("Use Demo Account", key="demo_login"):
            # Set session state with demo account
            st.session_state.user_id = 1  # Assuming demo account has ID 1
            st.session_state.username = "demo_user"
            
            # Show success message and redirect
            st.success("Logged in as demo user! Redirecting...")
            time.sleep(1)
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Additional information
        st.markdown("""
        <div class="info-text">
            Don't have an account? Select "Sign Up" from the sidebar to create one.
        </div>
        """, unsafe_allow_html=True)
