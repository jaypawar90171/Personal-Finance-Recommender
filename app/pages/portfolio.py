import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import sqlite3
from datetime import datetime, timedelta

st.markdown("""
    <style>
    .metric-card {
        padding: 1.5rem;
        border: 1px solid #23262b;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background: #181b20; /* Match dark background */
        color: #f3f6fa;      /* Light text for contrast */
        text-align: center;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: bold;
        color: #f3f6fa;
        margin-bottom: 0.5rem;
    }
    .metric-label {
        font-size: 1.1rem;
        color: #b0b8c1;
    }
    .metric-value.positive, .metric-label.positive {
        color: #4caf50;
    }
    .metric-value.negative, .metric-label.negative {
        color: #e57373;
    }     
    .stColumns {
        gap: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

def show_portfolio(user_id):
    st.markdown('<div class="main-header">Portfolio Management</div>', unsafe_allow_html=True)
    
    # Portfolio tabs
    portfolio_tabs = st.tabs(["Portfolio Overview", "Add to Portfolio"])
    
    with portfolio_tabs[0]:
        display_portfolio(user_id)
    
    with portfolio_tabs[1]:
        add_to_portfolio(user_id)

def display_portfolio(user_id):
   
    st.markdown('<div class="sub-header">Your Portfolio</div>', unsafe_allow_html=True)
    
    # Get portfolio data from database
    conn = sqlite3.connect('database/stock_analyzer.db')
    c = conn.cursor()
    
    c.execute("""
    SELECT id, ticker, shares, purchase_price, purchase_date
    FROM portfolio_items
    WHERE user_id = ?
    """, (user_id,))
    
    portfolio_items = c.fetchall()
    
    if not portfolio_items:
        st.info("Your portfolio is empty. Add stocks to track your investments.")
        conn.close()
        return
    # print("Hello")
    # Create portfolio dataframe
    portfolio_data = []
    total_value = 0
    total_cost = 0
    
    for item in portfolio_items:
        item_id, ticker, shares, purchase_price, purchase_date = item
        
        try:
            # Get current price
            current_data = yf.download(ticker, period="1d")
            if not current_data.empty:
                current_price = current_data['Close'].iloc[-1][0]
                
                cost_basis = shares * purchase_price
                current_value = shares * current_price
                gain_loss = current_value - cost_basis
                gain_loss_pct = (gain_loss / cost_basis) * 100
                
                total_value += current_value
                total_cost += cost_basis
               
                portfolio_data.append({
                    'ID': item_id,
                    'Ticker': ticker,
                    'Shares': shares,
                    'Purchase Price': f"${float(purchase_price):.2f}",
                    'Current Price': f"${current_price:.2f}",
                    'Cost Basis': f"${cost_basis:.2f}",
                    'Current Value': f"${current_value:.2f}",
                    'Gain/Loss': f"${gain_loss:.2f}",
                    'Gain/Loss %': f"{gain_loss_pct:.2f}%",
                    'Purchase Date': purchase_date
                })
        except Exception as e:
            st.error(f"Error fetching data for {ticker}: {e}")
    
    # Display portfolio summary
    if portfolio_data:
        total_gain_loss = total_value - total_cost
        total_gain_loss_pct = (total_gain_loss / total_cost) * 100 if total_cost > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">${total_value:.2f}</div>
                <div class="metric-label">Total Portfolio Value</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">${total_cost:.2f}</div>
                <div class="metric-label">Total Cost Basis</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            gain_loss_color = "positive" if total_gain_loss >= 0 else "negative"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value {gain_loss_color}">${total_gain_loss:.2f}</div>
                <div class="metric-label">Total Gain/Loss</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            gain_loss_pct_color = "positive" if total_gain_loss_pct >= 0 else "negative"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value {gain_loss_pct_color}">{total_gain_loss_pct:.2f}%</div>
                <div class="metric-label">Total Return</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Display portfolio table
        df = pd.DataFrame(portfolio_data)
        st.dataframe(df, use_container_width=True)
        
        # Portfolio allocation pie chart
        portfolio_allocation = []
        
        for item in portfolio_data:
            ticker = item['Ticker']
            current_value = float(item['Current Value'].replace('$', ''))
            allocation_pct = (current_value / total_value) * 100
            
            portfolio_allocation.append({
                'Ticker': ticker,
                'Value': current_value,
                'Allocation': allocation_pct
            })
        
        allocation_df = pd.DataFrame(portfolio_allocation)
        
        fig = px.pie(
            allocation_df,
            values='Allocation',
            names='Ticker',
            title='Portfolio Allocation',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hoverinfo='label+percent+value'
        )
        
        fig.update_layout(
            height=400,
            margin=dict(l=50, r=50, t=80, b=50),
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Option to remove stocks from portfolio
        st.markdown('<div class="sub-header">Remove from Portfolio</div>', unsafe_allow_html=True)
        
        ticker_to_remove = st.selectbox("Select Stock to Remove", [item['Ticker'] for item in portfolio_data])
        
        if st.button("Remove Selected Stock"):
            # Find the ID of the selected ticker
            item_id = next((item['ID'] for item in portfolio_data if item['Ticker'] == ticker_to_remove), None)
            
            if item_id:
                # Remove from database
                c.execute("DELETE FROM portfolio_items WHERE id = ?", (item_id,))
                conn.commit()
                
                st.success(f"Removed {ticker_to_remove} from your portfolio!")
                st.experimental_rerun()
    
    conn.close()

def add_to_portfolio(user_id):
    st.markdown('<div class="sub-header">Add to Portfolio</div>', unsafe_allow_html=True)
    
    # Check if we're adding a specific ticker from another page
    if 'add_to_portfolio' in st.session_state:
        ticker_default = st.session_state.add_to_portfolio
        st.session_state.add_to_portfolio = None  # Clear after using
    else:
        ticker_default = ""
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        ticker = st.text_input("Stock Ticker", value=ticker_default).upper()
    
    with col2:
        shares = st.number_input("Number of Shares", min_value=0.01, step=0.01)
    
    with col3:
        purchase_date = st.date_input("Purchase Date", datetime.now() - timedelta(days=0))
    
    if st.button("Add to Portfolio"):
        if ticker and shares > 0:
            # Fetch stock data to validate ticker and get purchase price
            try:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = purchase_date.strftime('%Y-%m-%d')
                
                stock_data = yf.download(ticker, start=start_date, end=end_date)
                
                if stock_data.empty:
                    st.error(f"No data found for ticker {ticker}")
                    return
                
                purchase_price = stock_data.iloc[0]['Close']
                
                # Add to database
                conn = sqlite3.connect('database/stock_analyzer.db')
                c = conn.cursor()
                
                # Check if already exists
                c.execute("SELECT id FROM portfolio_items WHERE user_id = ? AND ticker = ?", (user_id, ticker))
                existing = c.fetchone()
                print("Hello")
                if existing:
                    # Update existing entry
                    print("HEllo 1")
                    c.execute("""
                    UPDATE portfolio_items 
                    SET shares = shares + ?, purchase_price = (purchase_price * shares + ? * ?) / (shares + ?),
                    updated_at = datetime('now')
                    WHERE user_id = ? AND ticker = ?
                    """, (shares, purchase_price[0], shares, shares, user_id, ticker))
                    
                    st.success(f"Updated {ticker} in your portfolio!")
                else:
                    # Add new entry
                    # print(shares)
                    print("Purchase Price : ", purchase_price[0])
                    
                    c.execute("""
                    INSERT INTO portfolio_items (user_id, ticker, shares, purchase_price, purchase_date, created_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """, (user_id, ticker, shares, purchase_price[0], purchase_date.strftime('%Y-%m-%d')))
                    
                    st.success(f"Added {shares} shares of {ticker} to your portfolio!")
                
                conn.commit()
                conn.close()
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Error adding stock to portfolio: {e}")
        else:
            st.warning("Please enter a valid ticker and number of shares.")
