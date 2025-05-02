from datetime import datetime
import streamlit as st
import sqlite3
import hashlib
import pandas as pd

def show_settings(user_id):
    st.markdown('<div class="main-header">Settings</div>', unsafe_allow_html=True)
    
    # Settings tabs
    settings_tabs = st.tabs(["Account Settings", "Appearance", "Data Management", "Notifications"])
    
    with settings_tabs[0]:
        show_account_settings(user_id)
    
    with settings_tabs[1]:
        show_appearance_settings(user_id)
    
    with settings_tabs[2]:
        show_data_management(user_id)
    
    with settings_tabs[3]:
        show_notification_settings(user_id)

def show_account_settings(user_id):
    st.markdown('<div class="sub-header">Account Settings</div>', unsafe_allow_html=True)
    
    # Get user information
    conn = sqlite3.connect('database/stock_analyzer.db')
    c = conn.cursor()
    
    c.execute("SELECT username, email, full_name FROM users WHERE id = ?", (user_id,))
    user_data = c.fetchone()
    
    if not user_data:
        st.error("User data not found. Please try logging in again.")
        conn.close()
        return
    
    username, email, full_name = user_data
    
    # Display current account information
    st.markdown("""
    <div class="card">
        <h3>Current Account Information</h3>
        <p><strong>Username:</strong> {}</p>
        <p><strong>Email:</strong> {}</p>
        <p><strong>Full Name:</strong> {}</p>
    </div>
    """.format(username, email, full_name), unsafe_allow_html=True)
    
    # Update account information
    st.markdown('<div class="sub-header">Update Account Information</div>', unsafe_allow_html=True)
    
    new_full_name = st.text_input("Full Name", value=full_name)
    new_email = st.text_input("Email", value=email)
    
    if st.button("Update Account Information"):
        if new_full_name and new_email:
            c.execute("UPDATE users SET full_name = ?, email = ?, updated_at = datetime('now') WHERE id = ?", 
                     (new_full_name, new_email, user_id))
            conn.commit()
            st.success("Account information updated successfully!")
        else:
            st.error("Please fill in all fields.")
    
    # Change password
    st.markdown('<div class="sub-header">Change Password</div>', unsafe_allow_html=True)
    
    current_password = st.text_input("Current Password", type="password")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")
    
    if st.button("Change Password"):
        if current_password and new_password and confirm_password:
            if new_password != confirm_password:
                st.error("New passwords do not match.")
            elif len(new_password) < 8:
                st.error("New password must be at least 8 characters long.")
            else:
                # Verify current password
                hashed_current = hashlib.sha256(current_password.encode()).hexdigest()
                
                c.execute("SELECT id FROM users WHERE id = ? AND password = ?", (user_id, hashed_current))
                if c.fetchone():
                    # Update password
                    hashed_new = hashlib.sha256(new_password.encode()).hexdigest()
                    c.execute("UPDATE users SET password = ?, updated_at = datetime('now') WHERE id = ?", 
                             (hashed_new, user_id))
                    conn.commit()
                    st.success("Password changed successfully!")
                else:
                    st.error("Current password is incorrect.")
        else:
            st.error("Please fill in all password fields.")
    
    conn.close()

def show_appearance_settings(user_id):
    st.markdown('<div class="sub-header">Appearance Settings</div>', unsafe_allow_html=True)
    
    # Get current theme setting
    conn = sqlite3.connect('database/stock_analyzer.db')
    c = conn.cursor()
    
    c.execute("SELECT theme FROM user_settings WHERE user_id = ?", (user_id,))
    theme_data = c.fetchone()
    
    current_theme = theme_data[0] if theme_data else 'light'
    
    # Theme selection
    theme = st.radio("Select Theme", ["Light", "Dark"], index=0 if current_theme == 'light' else 1)
    
    if st.button("Save Theme"):
        new_theme = theme.lower()
        
        # Check if settings exist
        c.execute("SELECT id FROM user_settings WHERE user_id = ?", (user_id,))
        settings_exist = c.fetchone()
        
        if settings_exist:
            c.execute("UPDATE user_settings SET theme = ?, updated_at = datetime('now') WHERE user_id = ?", 
                     (new_theme, user_id))
        else:
            c.execute("INSERT INTO user_settings (user_id, theme, created_at) VALUES (?, ?, datetime('now'))", 
                     (user_id, new_theme))
        
        conn.commit()
        st.success("Theme updated successfully!")
        
        # Update session state
        st.session_state.theme = new_theme
        st.rerun()
    
    conn.close()

def show_data_management(user_id):
    st.markdown('<div class="sub-header">Data Management</div>', unsafe_allow_html=True)
    
    # Clear data options
    st.markdown("""
    <div class="card">
        <h3>Clear Data</h3>
        <p>You can clear various types of data from your account. This action cannot be undone.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Clear Portfolio"):
        conn = sqlite3.connect('database/stock_analyzer.db')
        c = conn.cursor()
        c.execute("DELETE FROM portfolio_items WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        st.success("Portfolio cleared!")
    
    if st.button("Clear Watchlist"):
        conn = sqlite3.connect('database/stock_analyzer.db')
        c = conn.cursor()
        c.execute("DELETE FROM watchlist_items WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        st.success("Watchlist cleared!")
    
    if st.button("Reset Risk Assessment"):
        conn = sqlite3.connect('database/stock_analyzer.db')
        c = conn.cursor()
        c.execute("DELETE FROM risk_assessments WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        st.success("Risk assessment reset!")
    
    if st.button("Clear Chat History"):
        conn = sqlite3.connect('database/stock_analyzer.db')
        c = conn.cursor()
        c.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        # Clear chat history in session state
        if 'chat_history' in st.session_state:
            st.session_state.chat_history = [
                {
                    "message": "Hello! I'm your AI investment assistant. How can I help you today?",
                    "is_user": False,
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            ]
        
        st.success("Chat history cleared!")
    
    if st.button("Reset All Data"):
        conn = sqlite3.connect('database/stock_analyzer.db')
        c = conn.cursor()
        c.execute("DELETE FROM portfolio_items WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM watchlist_items WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM risk_assessments WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM selected_stocks WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        # Clear session state
        if 'selected_stocks' in st.session_state:
            st.session_state.selected_stocks = []
        
        if 'chat_history' in st.session_state:
            st.session_state.chat_history = [
                {
                    "message": "Hello! I'm your AI investment assistant. How can I help you today?",
                    "is_user": False,
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            ]
        
        st.success("All data reset!")
    
    # Export data
    st.markdown('<div class="sub-header">Export Data</div>', unsafe_allow_html=True)
    
    if st.button("Export Portfolio Data"):
        conn = sqlite3.connect('database/stock_analyzer.db')
        query = "SELECT ticker, shares, purchase_price, purchase_date FROM portfolio_items WHERE user_id = ?"
        portfolio_df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        
        if not portfolio_df.empty:
            csv = portfolio_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="portfolio_data.csv",
                mime="text/csv"
            )
        else:
            st.info("No portfolio data to export.")

def show_notification_settings(user_id):
    st.markdown('<div class="sub-header">Notification Settings</div>', unsafe_allow_html=True)
    
    # Get current notification settings
    conn = sqlite3.connect('database/stock_analyzer.db')
    c = conn.cursor()
    
    c.execute("SELECT email_notifications, price_alerts FROM user_settings WHERE user_id = ?", (user_id,))
    notification_data = c.fetchone()
    
    email_notifications = notification_data[0] if notification_data and notification_data[0] is not None else 1
    price_alerts = notification_data[1] if notification_data and notification_data[1] is not None else 1
    
    # Notification options
    st.markdown("""
    <div class="card">
        <h3>Email Notifications</h3>
        <p>Configure which email notifications you'd like to receive.</p>
    </div>
    """, unsafe_allow_html=True)
    
    email_notifications_enabled = st.checkbox("Enable Email Notifications", value=bool(email_notifications))
    price_alerts_enabled = st.checkbox("Enable Price Alerts", value=bool(price_alerts))
    
    if st.button("Save Notification Settings"):
        # Check if settings exist
        c.execute("SELECT id FROM user_settings WHERE user_id = ?", (user_id,))
        settings_exist = c.fetchone()
        
        if settings_exist:
            c.execute("""
            UPDATE user_settings 
            SET email_notifications = ?, price_alerts = ?, updated_at = datetime('now') 
            WHERE user_id = ?
            """, (int(email_notifications_enabled), int(price_alerts_enabled), user_id))
        else:
            c.execute("""
            INSERT INTO user_settings (user_id, email_notifications, price_alerts, created_at) 
            VALUES (?, ?, ?, datetime('now'))
            """, (user_id, int(email_notifications_enabled), int(price_alerts_enabled)))
        
        conn.commit()
        st.success("Notification settings updated successfully!")
    
    conn.close()
