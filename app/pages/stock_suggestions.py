import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import sqlite3
from utils.stock_analyzer import StockAnalyzer
from utils.stock_utils import get_company_logo, get_stock_news

def show_stock_suggestions(user_id):
    st.markdown('<div class="main-header">Stock Suggestions</div>', unsafe_allow_html=True)
    
    # Initialize analyzer if not already done
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = StockAnalyzer()
    
    # Get user's risk profile
    conn = sqlite3.connect('database/stock_analyzer.db')
    c = conn.cursor()
    
    c.execute("""
    SELECT risk_score, risk_profile, risk_description 
    FROM risk_assessments 
    WHERE user_id = ? 
    ORDER BY created_at DESC 
    LIMIT 1
    """, (user_id,))
    risk_data = c.fetchone()
    
    if not risk_data:
        st.warning("Please complete the risk assessment first to get personalized stock suggestions.")
        if st.button("Go to Risk Assessment"):
            st.session_state.page = "Risk Assessment"
            st.experimental_rerun()
        return
    
    risk_score, risk_profile, risk_description = risk_data
    
    # Display risk profile
    st.markdown(f"""
    <div class="card">
        <h3>Your Risk Profile</h3>
        <h4>{risk_profile}</h4>
        <div class="progress-bar">
            <div class="progress" style="width: {risk_score}%;"></div>
        </div>
        <p>{risk_description}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get current portfolio
    c.execute("""
    SELECT ticker, shares 
    FROM portfolio_items 
    WHERE user_id = ?
    """, (user_id,))
    portfolio_items = c.fetchall()
    
    # Get sectors and industries in current portfolio
    portfolio_sectors = {}
    portfolio_tickers = [item[0] for item in portfolio_items]
    
    for ticker in portfolio_tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            sector = info.get('sector', 'Unknown')
            if sector in portfolio_sectors:
                portfolio_sectors[sector] += 1
            else:
                portfolio_sectors[sector] = 1
        except:
            continue
    
    # Define stock universes based on risk profile
    stock_universes = {
        'Conservative': [
            'MSFT', 'JNJ', 'PG', 'KO', 'PEP', 'WMT', 'VZ', 'MRK', 'PFE', 'CSCO',  # Blue chips
            'VIG', 'NOBL', 'SDY', 'DVY', 'VYM'  # Dividend ETFs
        ],
        'Moderately Conservative': [
            'AAPL', 'HD', 'UNH', 'CVX', 'ABT', 'TMO', 'DHR', 'LIN', 'AVGO', 'MCD',
            'VTI', 'VEA', 'VTV', 'SCHD', 'IWF'
        ],
        'Moderate': [
            'GOOGL', 'V', 'MA', 'DIS', 'ADBE', 'NFLX', 'PYPL', 'INTC', 'AMD', 'QCOM',
            'QQQ', 'SPY', 'IWM', 'VGT', 'XLK'
        ],
        'Moderately Aggressive': [
            'NVDA', 'TSM', 'SQ', 'SHOP', 'ABNB', 'UBER', 'SNAP', 'DDOG', 'CRWD', 'NET',
            'ARKK', 'ARKG', 'ARKF', 'SOXX', 'IGV'
        ],
        'Aggressive': [
            'TSLA', 'COIN', 'MSTR', 'RBLX', 'U', 'UPST', 'AFRM', 'HOOD', 'PLTR', 'LCID',
            'BITW', 'BLOK', 'MOON', 'YOLO', 'IPO'
        ]
    }
    
    def get_risk_based_universe(risk_score):
        if risk_score < 30:
            return stock_universes['Conservative']
        elif risk_score < 50:
            return stock_universes['Moderately Conservative']
        elif risk_score < 70:
            return stock_universes['Moderate']
        elif risk_score < 85:
            return stock_universes['Moderately Aggressive']
        else:
            return stock_universes['Aggressive']
    
    # Get suggested stocks based on risk profile
    suggested_universe = get_risk_based_universe(risk_score)
    
    # Analyze suggested stocks
    st.markdown('<div class="sub-header">Suggested Stocks</div>', unsafe_allow_html=True)
    
    suggestions = []
    
    with st.spinner("Analyzing stocks that match your risk profile..."):
        for ticker in suggested_universe:
            if ticker in portfolio_tickers:
                continue  # Skip stocks already in portfolio
                
            try:
                # Get stock data and risk metrics
                data = st.session_state.analyzer.fetch_stock_data(ticker, period="1y")
                if data is None or data.empty:
                    continue
                    
                risk_metrics = st.session_state.analyzer.calculate_risk_metrics(data)
                suitability = st.session_state.analyzer.evaluate_stock_suitability(
                    ticker, 
                    risk_metrics,
                    {"score": risk_score, "profile": risk_profile}
                )
                
                if suitability and suitability['Overall Suitability Score'] >= 70:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    suggestions.append({
                        'Ticker': ticker,
                        'Name': info.get('shortName', ticker),
                        'Sector': info.get('sector', 'N/A'),
                        'Suitability Score': suitability['Overall Suitability Score'],
                        'Match Rating': suitability['Match Rating'],
                        'Current Price': info.get('currentPrice', 0),
                        'Market Cap': info.get('marketCap', 0),
                        'Beta': risk_metrics.get('Beta', 0),
                        'Volatility': risk_metrics.get('Volatility (Annual)', 0) * 100
                    })
                    
                if len(suggestions) >= 5:  # Limit to top 5 suggestions
                    break
                    
            except Exception as e:
                print(f"Error analyzing {ticker}: {str(e)}")
                continue
    
    if suggestions:
        # Sort by suitability score
        suggestions.sort(key=lambda x: x['Suitability Score'], reverse=True)
        
        # Display suggestions
        for stock in suggestions:
            col1, col2 = st.columns([1, 3])
            
            with col1:
                logo_url = get_company_logo(stock['Ticker'])
                st.image(logo_url, width=80)
            
            with col2:
                st.markdown(f"""
                <div class="stock-suggestion-card">
                    <h3>{stock['Name']} ({stock['Ticker']})</h3>
                    <p>Sector: {stock['Sector']}</p>
                    <p>Suitability Score: <span class="positive">{stock['Suitability Score']:.2f}/100</span></p>
                    <p>Match Rating: {stock['Match Rating']}</p>
                    <p>Current Price: ${stock['Current Price']:.2f}</p>
                    <p>Beta: {stock['Beta']:.2f} | Volatility: {stock['Volatility']:.2f}%</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Analyze {stock['Ticker']}", key=stock['Ticker']):
                    st.session_state.stock_to_analyze = stock['Ticker']
                    st.session_state.page = "Stock Analysis"
                    st.experimental_rerun()
    else:
        st.info("No suitable stock suggestions found. Try adjusting your risk profile or portfolio criteria.")
    
    conn.close()