from datetime import datetime
import streamlit as st
import pandas as pd
import yfinance as yf
import sqlite3
from utils.stock_utils import get_company_logo
import smtplib
from email.message import EmailMessage
import time

st.markdown("""
<style>
.card {
    padding: 1.5rem;
    border: 1px solid #23262b;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    background: #181b20;   /* Match dark background */
    color: #f3f6fa;        /* Light text for contrast */
    text-align: center;
}
.card h3 {
    color: #e0e6ed;
    font-size: 2rem;
    margin-bottom: 0.5rem;
    margin-top: 0;
    font-weight: 700;
    letter-spacing: 1px;
}
.card p {
    color: #b0b8c1;
    font-size: 1.1rem;
    margin: 0.5rem 0;
}
.card h2 {
    color: #f3f6fa;
    font-size: 2rem;
    margin: 0.5rem 0;
}
.card .positive {
    color: #4caf50;
    font-size: 1.1rem;
    font-weight: 600;
}
.card .negative {
    color: #e57373;
    font-size: 1.1rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

def send_watchlist_email(to_email, ticker):
    msg = EmailMessage()
    msg['Subject'] = f"Confirmation: Stock Added to Your Watchlist:  {ticker}"
    msg['From'] = "apg111331@gmail.com"
    msg['To'] = to_email
    message  = f""" Dear Valued Client,

        We are pleased to confirm that the following stock has been successfully added to your watchlist:

        Stock Name: {ticker} 
        Date Added: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        You can monitor this stock and manage your watchlist at any time through your account dashboard.

        Thank you for choosing our platform. If you have any questions, please contact our support team at support@example.com.

        Best regards,

        Finance Recommender

        © 2025 Finance Recommender. All rights reserved."""
    

    
    msg.set_content(message)

    # For Gmail, you may need an app password if 2FA is enabled
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login("apg111331@gmail.com", "wcxa pfif frdu fyrn")
        smtp.send_message(msg)

def show_watchlist(user_id):
    conn = sqlite3.connect('database/stock_analyzer.db')
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    user_email = c.fetchone()[0]
    conn.close()

    st.markdown('<div class="main-header">Watchlist</div>', unsafe_allow_html=True)
    
    # Watchlist tabs
    watchlist_tabs = st.tabs(["Your Watchlist", "Add to Watchlist"])
    
    with watchlist_tabs[0]:
        display_watchlist(user_id)
    
    with watchlist_tabs[1]:
        add_to_watchlist(user_id, user_email)

def display_watchlist(user_id):
    st.markdown('<div class="sub-header">Your Watchlist</div>', unsafe_allow_html=True)
    
    # Get watchlist from database
    conn = sqlite3.connect('database/stock_analyzer.db')
    c = conn.cursor()
    
    c.execute("""
    SELECT id, ticker, added_at
    FROM watchlist_items
    WHERE user_id = ?
    """, (user_id,))
    
    watchlist_items = c.fetchall()
    conn.close()
    
    if not watchlist_items:
        st.info("Your watchlist is empty. Add stocks to track them.")
        return
    
    # Fetch current data for watchlist stocks
    watchlist_data = []
    
    for item in watchlist_items:
        item_id, ticker, added_at = item
        
        try:
            # Get current price data
            current_data = yf.download(ticker, period="2d")
            
            if not current_data.empty and len(current_data) >= 2:
                current_price = current_data['Close'].iloc[-1]
                prev_price = current_data['Close'].iloc[-2]
                price_change = current_price - prev_price
                price_change_pct = (price_change / prev_price) * 100
                
                # Get company info
                stock = yf.Ticker(ticker)
                info = stock.info
                company_name = info.get('shortName', ticker)
                
                watchlist_data.append({
                    'ID': item_id,
                    'Ticker': ticker,
                    'Company': company_name,
                    'Price': current_price,
                    'Change': price_change,
                    'Change %': price_change_pct
                })
        except Exception as e:
            watchlist_data.append({
                'ID': item_id,
                'Ticker': ticker,
                'Company': ticker,
                'Price': 0,
                'Change': 0,
                'Change %': 0
            })
    
    # Display watchlist as cards
    cols = st.columns(3)
    
    for i, stock in enumerate(watchlist_data):
        col = cols[i % 3]
        
        with col:
            
            change_color = "positive" if (stock['Change']).any() else "negative"
            change_icon = "↑" if (stock['Change']).any() else "↓"
            
            st.markdown(f"""
            <div class="card">
                <h3>{stock['Ticker']}</h3>
                <p>{stock['Company']}</p>
                <h2>${float(stock['Price']):.2f}</h2>
                <p class="{change_color}">{change_icon} ${abs(float(stock['Change'])):.2f} ({float(stock['Change %']):.2f}%)</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Option to remove stocks from watchlist
    st.markdown('<div class="sub-header">Remove from Watchlist</div>', unsafe_allow_html=True)
    
    ticker_to_remove = st.selectbox("Select Stock to Remove", [stock['Ticker'] for stock in watchlist_data])
    
    if st.button("Remove from Watchlist"):
        # Find the ID of the selected ticker
        item_id = next((stock['ID'] for stock in watchlist_data if stock['Ticker'] == ticker_to_remove), None)
        
        if item_id:
            # Remove from database
            conn = sqlite3.connect('database/stock_analyzer.db')
            c = conn.cursor()
            c.execute("DELETE FROM watchlist_items WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            
            st.success(f"Removed {ticker_to_remove} from your watchlist!")
            st.rerun()

def add_to_watchlist(user_id, user_email):
    st.markdown('<div class="sub-header">Add to Watchlist</div>', unsafe_allow_html=True)
    
    ticker = st.text_input("Stock Ticker", key="watchlist_ticker").upper()
    
    if st.button("Add to Watchlist"):
        if ticker:
            # Validate ticker
            try:
                stock_data = yf.download(ticker, period="1d")
                
                if stock_data.empty:
                    st.error(f"No data found for ticker {ticker}")
                    return
                
                # Check if already in watchlist
                conn = sqlite3.connect('database/stock_analyzer.db')
                c = conn.cursor()
                
                c.execute("SELECT id FROM watchlist_items WHERE user_id = ? AND ticker = ?", (user_id, ticker))
                existing = c.fetchone()
                
                if existing:
                    st.info(f"{ticker} is already in your watchlist.")
                else:
                    # Add to watchlist
                    c.execute("""
                    INSERT INTO watchlist_items (user_id, ticker, added_at)
                    VALUES (?, ?, datetime('now'))
                    """, (user_id, ticker))
                    conn.commit()
                    # Fetch user email
                    c.execute("SELECT email FROM users WHERE id = ?", (user_id,))
                    user_email = c.fetchone()[0]
                    conn.close()
                    # Send notification email
                    send_watchlist_email(user_email, ticker)
                    # Show success message
                    st.success(f"Added {ticker} to your watchlist!")
                    time.sleep(1)  # Wait 1 second so user sees the message
                    st.rerun()
                
            except Exception as e:
                st.error(f"Error adding stock to watchlist: {e}")
        else:
            st.warning("Please enter a valid ticker.")
