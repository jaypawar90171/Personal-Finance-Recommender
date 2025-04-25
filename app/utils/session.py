import streamlit as st

def check_session():
    """Check if user is logged in and return user_id and username"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    return st.session_state.user_id, st.session_state.username
