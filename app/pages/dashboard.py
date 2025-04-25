import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
from utils.stock_utils import get_company_logo, get_stock_news

def safe_float_convert(value):
    """Safely convert value to float, handling Series and NaN values"""
    if isinstance(value, pd.Series):
        return float(value.iloc[0]) if not value.empty and pd.notnull(value.iloc[0]) else 0.0
    return float(value) if pd.notnull(value) else 0.0

def show_dashboard(user_id):
    st.markdown("""
    <style>
    .news-card {
        padding: 1rem;
        border: 1px solid #23262b;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background: #181b20;
        color: #f3f6fa;
    }
    .news-header h4 {
        margin: 0;
        color: #f3f6fa;
        font-size: 1.1rem;
    }
    .news-meta {
        font-size: 0.8rem;
        color: #b0b8c1;
    }
    .news-footer {
        margin-top: 0.5rem;
    }
    .news-footer a {
        color: #90caf9;
        text-decoration: none;
    }
    .news-footer a:hover {
        text-decoration: underline;
    }
    .metric-card {
        padding: 1.5rem;
        border: 1px solid #23262b;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background: #181b20;
        color: #f3f6fa;
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
    .metric-label.positive {
        color: #4caf50;
    }
    .metric-label.negative {
        color: #e57373;
    }
    .card {
        padding: 1.5rem;
        border: 1px solid #23262b;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background: #181b20;
        color: #f3f6fa;
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
    .card .positive {
        color: #4caf50;
        font-size: 1.2rem;
        font-weight: 600;
    }
    .card .negative {
        color: #e57373;
        font-size: 1.2rem;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header">Market Dashboard</div>', unsafe_allow_html=True)
    
    # Market overview
    st.markdown('<div class="sub-header">Market Overview</div>', unsafe_allow_html=True)
    
    # Fetch major indices data
    indices = {
        '^GSPC': 'S&P 500',
        '^DJI': 'Dow Jones',
        '^IXIC': 'NASDAQ',
        '^RUT': 'Russell 2000'
    }
    
    indices_data = []
    
    for ticker, name in indices.items():
        try:
            data = yf.download(ticker, period="2d")
            if not data.empty and len(data) >= 2:
                current = data['Close'].iloc[-1]
                prev = data['Close'].iloc[-2]
                change = current - prev
                change_pct = (change / prev) * 100
                
                indices_data.append({
                    'Index': name,
                    'Price': current,
                    'Change': change,
                    'Change %': change_pct
                })
        except:
            pass
    
    # Display indices as cards
    cols = st.columns(len(indices_data))
    
    for i, idx in enumerate(indices_data):
        with cols[i]:
            change_color = "positive" if (idx['Change'] >= 0).all() else "negative"

            change_icon = "↑" if (idx['Change'] >= 0).all() else "↓"
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>{idx['Index']}</h3>
                <div class="metric-label {change_color}">{change_icon} {abs(idx['Price'].iloc[0]):.2f} ({idx['Change %'].iloc[0]:.2f}%)</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Top gainers and losers
    st.markdown('<div class="sub-header">Top Movers Today</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h3>Top Gainers</h3>', unsafe_allow_html=True)
        try:
            # This is a placeholder - in a real app, you'd use a proper API to get top gainers
            gainers = [
                {'Ticker': 'AAPL', 'Change %': 2.5},
                {'Ticker': 'MSFT', 'Change %': 1.8},
                {'Ticker': 'AMZN', 'Change %': 1.5}
            ]
            
            for gainer in gainers:
                st.markdown(f"""
                <div class="card">
                    <h3>{gainer['Ticker']}</h3>
                    <p class="positive">↑ {gainer['Change %']}%</p>
                </div>
                """, unsafe_allow_html=True)
        except:
            st.info("Unable to fetch top gainers data.")
    
    with col2:
        st.markdown('<h3>Top Losers</h3>', unsafe_allow_html=True)
        try:
            # This is a placeholder - in a real app, you'd use a proper API to get top losers
            losers = [
                {'Ticker': 'NFLX', 'Change %': -1.8},
                {'Ticker': 'TSLA', 'Change %': -1.5},
                {'Ticker': 'META', 'Change %': -1.2}
            ]
            
            for loser in losers:
                st.markdown(f"""
                <div class="card">
                    <h3>{loser['Ticker']}</h3>
                    <p class="negative">↓ {abs(loser['Change %'])}%</p>
                </div>
                """, unsafe_allow_html=True)
        except:
            st.info("Unable to fetch top losers data.")
    
    # Portfolio summary if available
    conn = sqlite3.connect('database/stock_analyzer.db')
    c = conn.cursor()
    
    # Check if user has portfolio items
    c.execute("SELECT COUNT(*) FROM portfolio_items WHERE user_id = ?", (user_id,))
    portfolio_count = c.fetchone()[0]
    
    if portfolio_count > 0:
        st.markdown('<div class="sub-header">Your Portfolio Summary</div>', unsafe_allow_html=True)
        
        # Get portfolio data
        c.execute("""
        SELECT ticker, shares, purchase_price, purchase_date
        FROM portfolio_items
        WHERE user_id = ?
        """, (user_id,))
        
        portfolio_items = c.fetchall()
        
        # Calculate portfolio metrics
        total_value = 0
        total_cost = 0
        portfolio_allocation = []
        
        for item in portfolio_items:
            ticker, shares, purchase_price, purchase_date = item
            
            # Get current price
            try:
                current_data = yf.download(ticker, period="1d")
                if not current_data.empty:
                    current_price = safe_float_convert(current_data['Close'].iloc[-1])
                    
                    item_cost = shares * purchase_price
                    item_value = shares * current_price
                    
                    total_cost = safe_float_convert(total_cost)
                    total_value = safe_float_convert(total_value)
                    
                    total_cost += item_cost
                    total_value += item_value
                    
                    portfolio_allocation.append({
                        'Ticker': ticker,
                        'Value': item_value,
                        'Allocation': 0  # Will calculate after total is known
                    })
            except Exception as e:
                st.warning(f"Could not fetch data for {ticker}: {str(e)}")
                continue
        
        # Calculate allocation percentages
        if total_value > 0:
            for item in portfolio_allocation:
                item['Value'] = safe_float_convert(item['Value'])
                item['Allocation'] = (item['Value'] / total_value) * 100
        
        # Display portfolio metrics
        col1, col2 = st.columns(2)
        
        with col1:
            total_gain_loss = total_value - total_cost
            total_gain_loss_pct = (total_gain_loss / total_cost) * 100 if total_cost > 0 else 0
            
            gain_loss_color = "positive" if total_gain_loss >= 0 else "negative"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">${total_value:,.2f}</div>
                <div class="metric-label">Portfolio Value</div>
                <div class="metric-label {gain_loss_color}">
                    {'+' if total_gain_loss >= 0 else ''}{total_gain_loss:,.2f} ({total_gain_loss_pct:.2f}%)
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Create a simple portfolio allocation chart
            allocation_df = pd.DataFrame(portfolio_allocation)
            
            if not allocation_df.empty:
                fig = px.pie(
                    allocation_df,
                    values='Allocation',
                    names='Ticker',
                    title='',
                    hole=0.4
                )
                
                fig.update_layout(
                    showlegend=False,
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=200
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    conn.close()
    
    # Recent news
    st.markdown('<div class="sub-header">Recent Market News</div>', unsafe_allow_html=True)
    
    try:
        # Get news for S&P 500 as a proxy for market news
        market_news = get_stock_news('^GSPC', limit=5)
        
        if not market_news:
            st.info("No market news available at the moment.")
        else:
            for news_item in market_news:
                if not isinstance(news_item, dict):
                    continue
                    
                title = news_item.get('title', '')
                publisher = news_item.get('publisher', '')
                link = news_item.get('link', '')
                date = news_item.get('published', '')
                
                if not title or not link:
                    continue
                    
                st.markdown(f"""
                <div class="news-card">
                    <div class="news-header">
                        <h4>{title}</h4>
                        <span class="news-meta">{publisher} • {date}</span>
                    </div>
                    <div class="news-footer">
                        <a href="{link}" target="_blank" rel="noopener noreferrer">Read more →</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Unable to fetch market news: {str(e)}")
        # Log the error for debugging
        print(f"News fetching error: {str(e)}")
