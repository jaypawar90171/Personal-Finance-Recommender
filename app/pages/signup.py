import streamlit as st
import sqlite3
import hashlib
import time
import re

def show_signup():
    st.markdown('<div class="main-header">Create Your Account</div>', unsafe_allow_html=True)
    
    # Create a centered signup form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        # Signup form
        full_name = st.text_input("Full Name", key="signup_name")
        email = st.text_input("Email", key="signup_email")
        username = st.text_input("Username", key="signup_username")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
        
        # Error message placeholder
        error_placeholder = st.empty()
        
        # Signup button
        if st.button("Sign Up", key="signup_button"):
            # Validate inputs
            if not (full_name and email and username and password and confirm_password):
                error_placeholder.error("Please fill in all fields.")
            elif password != confirm_password:
                error_placeholder.error("Passwords do not match.")
            elif len(password) < 8:
                error_placeholder.error("Password must be at least 8 characters long.")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                error_placeholder.error("Please enter a valid email address.")
            else:
                # Check if username or email already exists
                conn = sqlite3.connect('database/stock_analyzer.db')
                c = conn.cursor()
                c.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
                existing_user = c.fetchone()
                
                if existing_user:
                    conn.close()
                    error_placeholder.error("Username or email already exists. Please choose another.")
                else:
                    # Hash the password
                    hashed_password = hashlib.sha256(password.encode()).hexdigest()
                    
                    # Insert new user
                    c.execute("""
                    INSERT INTO users (full_name, email, username, password, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                    """, (full_name, email, username, hashed_password))
                    
                    # Get the new user ID
                    user_id = c.lastrowid
                    
                    conn.commit()
                    conn.close()
                    
                    # Set session state
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    
                    # Show success message and redirect
                    st.success("Account created successfully! Redirecting...")
                    time.sleep(1)
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Additional information
        st.markdown("""
        <div class="info-text">
            Already have an account? Select "Login" from the sidebar to sign in.
        </div>
        """, unsafe_allow_html=True)
