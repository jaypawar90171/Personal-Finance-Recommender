import streamlit as st

# Set page configuration (must be first Streamlit command)
st.set_page_config(
    page_title="Advanced Stock Analysis Tool",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

import sqlite3
import os
from pages.login import show_login
from pages.signup import show_signup
from pages.dashboard import show_dashboard
from pages.stock_analysis import show_stock_analysis
from pages.portfolio import show_portfolio
from pages.watchlist import show_watchlist
from pages.risk_assessment import show_risk_assessment
from pages.education import show_education
# from pages.chatbot import show_chatbot
from pages.about import show_about
from pages.settings import show_settings
from utils.database import init_db
from utils.session import check_session
from pages.assistant import show_assistant

# Initialize database if it doesn't exist
init_db()

# Custom CSS for styling
with open("static/css/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Check if user is logged in
user_id, username = check_session()

# Main application
def main():
    # If user is not logged in, show login/signup pages
    if not user_id:
        # Sidebar for login/signup navigation
        with st.sidebar:
            st.image("static/images/logo.jpg", width=80)
            st.markdown("<h1 style='text-align: center; margin-top: -10px;'>Stock Analyzer</h1>", unsafe_allow_html=True)
            st.markdown("---")
            
            auth_option = st.radio("", ["Login", "Sign Up"])
        
        if auth_option == "Login":
            show_login()
        else:
            show_signup()
    
    # If user is logged in, show main application
    else:
        # Sidebar for navigation
        with st.sidebar:
            st.image("static/images/logo.jpg", width=80)
            st.markdown(f"<h1 style='text-align: center; margin-top: -10px;'>Stock Analyzer</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;'>Welcome, {username}!</p>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Navigation
            page = st.radio("Navigation", [
                "Dashboard", 
                "Stock Analysis", 
                "Portfolio", 
                "Watchlist", 
                "Risk Assessment",
                "Education Center",
                "AI Assistant",
                "About Us",
                "Settings"
            ])
            
            st.markdown("---")
            
            # Logout button
            if st.button("Logout"):
                st.session_state.user_id = None
                st.session_state.username = None
                st.experimental_rerun()
            
            # Get user's risk profile from database
            conn = sqlite3.connect('database/stock_analyzer.db')
            c = conn.cursor()
            c.execute("SELECT risk_score, risk_profile FROM risk_assessments WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
            risk_data = c.fetchone()
            conn.close()
            
            # Display risk profile if available
            if risk_data:
                st.markdown("---")
                st.markdown("<h3>Your Risk Profile</h3>", unsafe_allow_html=True)
                
                risk_score = risk_data[0]
                risk_profile = risk_data[1]
                
                # Create a progress bar for risk score
                st.markdown(f"<p>Risk Score: {risk_score:.1f}%</p>", unsafe_allow_html=True)
                st.progress(risk_score/100)
                st.markdown(f"<p>Profile: {risk_profile}</p>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("<div class='footer'>© 2023 Stock Analyzer</div>", unsafe_allow_html=True)
        
        # Main content based on selected page
        if page == "Dashboard":
            show_dashboard(user_id)
        elif page == "Stock Analysis":
            show_stock_analysis(user_id)
        elif page == "Portfolio":
            show_portfolio(user_id)
        elif page == "Watchlist":
            show_watchlist(user_id)
        elif page == "Risk Assessment":
            show_risk_assessment(user_id)
        elif page == "Education Center":
            show_education(user_id)
        elif page == "AI Assistant":
            show_assistant(user_id)
        elif page == "About Us":
            show_about()
        elif page == "Settings":
            show_settings(user_id)

if __name__ == "__main__":
    main()
