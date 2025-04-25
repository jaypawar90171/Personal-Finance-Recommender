import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from utils.chatbot_model import StockChatbotModel

def show_chatbot(user_id):
    st.markdown('<div class="main-header">AI Investment Assistant</div>', unsafe_allow_html=True)
    
    # Introduction
    st.markdown("""
    <div class="card">
        <h3>Your Personal Investment Assistant</h3>
        <p>
            Ask questions about stocks, investment strategies, or get personalized recommendations based on your risk profile.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize chatbot model if not already done
    if 'chatbot_model' not in st.session_state:
        with st.spinner("Initializing AI model..."):
            st.session_state.chatbot_model = StockChatbotModel()
    
    # Initialize chat history if not already done
    if 'chat_history' not in st.session_state:
        # Check if user has chat history in database
        conn = sqlite3.connect('database/stock_analyzer.db')
        c = conn.cursor()
        
        c.execute("""
        SELECT message, is_user, timestamp
        FROM chat_messages
        WHERE user_id = ?
        ORDER BY timestamp ASC
        LIMIT 20
        """, (user_id,))
        
        messages = c.fetchall()
        conn.close()
        
        if messages:
            st.session_state.chat_history = [
                {"message": msg[0], "is_user": bool(msg[1]), "timestamp": msg[2]}
                for msg in messages
            ]
        else:
            # Initialize with welcome message
            st.session_state.chat_history = [
                {
                    "message": "Hello! I'm your AI investment assistant. How can I help you today?",
                    "is_user": False,
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            ]
    
    # User input handling with proper state management
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "user_input" not in st.session_state:
        st.session_state.user_input = ""

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message["is_user"]:
                st.markdown(f"""
                <div class="chat-message user-message">
                    <div class="message-content">{message["message"]}</div>
                    <div class="message-timestamp">{message["timestamp"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <div class="message-content">{message["message"]}</div>
                    <div class="message-timestamp">{message["timestamp"]}</div>
                </div>
                """, unsafe_allow_html=True)

    # Create columns for input and button
    col1, col2 = st.columns([5,1])
    
    with col1:
        user_input = st.text_input("Ask a question", key="input_field")
    
    with col2:
        send_button = st.button("Send")

    if send_button and user_input.strip():
        try:
            # Process the message
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with sqlite3.connect('database/stock_analyzer.db') as conn:
                c = conn.cursor()
                
                # Add user message to chat history
                st.session_state.chat_history.append({
                    "message": user_input,
                    "is_user": True,
                    "timestamp": timestamp
                })
                
                # Save user message to database
                c.execute("""
                INSERT INTO chat_messages (user_id, message, is_user, timestamp)
                VALUES (?, ?, ?, ?)
                """, (user_id, user_input, True, timestamp))
                
                # Process query and get response
                try:
                    response = process_query(user_input, user_id)
                except Exception as e:
                    response = f"I apologize, but I encountered an error: {str(e)}"
                
                # Add assistant response
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                st.session_state.chat_history.append({
                    "message": response,
                    "is_user": False,
                    "timestamp": timestamp
                })
                
                # Save assistant response to database
                c.execute("""
                INSERT INTO chat_messages (user_id, message, is_user, timestamp)
                VALUES (?, ?, ?, ?)
                """, (user_id, response, False, timestamp))
                
                conn.commit()
            
            # Force a rerun to update the chat
            st.rerun()
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# In app/pages/chatbot.py, find this section in the process_query function:
def process_query(query, user_id):
    """Process user query and generate response"""
    try:
        query = query.strip().lower()
        
        # Convert Series to float when needed
        def safe_convert(series):
            if isinstance(series, pd.Series):
                return float(series.iloc[0])
            return float(series)
        
        # Add helper function for data processing
        def process_stock_data(data):
            if isinstance(data.index, pd.DatetimeIndex):
                data = data.reset_index()
            return data
        
        # Get user's risk profile from database
        with sqlite3.connect('database/stock_analyzer.db') as conn:
            c = conn.cursor()
            c.execute("SELECT risk_profile FROM risk_assessments WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
            risk_profile_data = c.fetchone()
        
        risk_profile = risk_profile_data[0] if risk_profile_data else "Moderate"
        
        # Check for special commands
        if "help" in query:
            return "I can help you with:\n- Stock analysis\n- Investment recommendations\n- Market insights\n- Risk assessment"
        
        # Use the chatbot model to process the query
        try:
            return st.session_state.chatbot_model.process_query(query, risk_profile)
        except Exception as e:
            return f"I apologize, but I couldn't process your query. Error: {str(e)}"
            
    except Exception as e:
        return f"I encountered an error while processing your request: {str(e)}"

def generate_stock_recommendation(user_id):
    """Generate stock recommendations based on user's risk profile"""
    # Get user's risk profile from database
    conn = sqlite3.connect('database/stock_analyzer.db')
    c = conn.cursor()
    
    c.execute("SELECT risk_profile FROM risk_assessments WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
    risk_profile_data = c.fetchone()
    conn.close()
    
    if not risk_profile_data:
        return "I need to understand your risk tolerance before making recommendations. Please complete the Risk Assessment in the Risk Assessment section."
    
    risk_profile = risk_profile_data[0]
    
    # Define stock universes based on risk profile
    stock_universes = {
        "Conservative": ["AAPL", "MSFT", "JNJ", "PG", "KO", "PEP", "VZ", "T", "PFE", "MRK"],
        "Moderately Conservative": ["AMZN", "GOOGL", "V", "MA", "HD", "UNH", "DIS", "CSCO", "INTC", "CMCSA"],
        "Moderate": ["META", "ADBE", "PYPL", "NFLX", "CRM", "NVDA", "AMD", "QCOM", "TXN", "AVGO"],
        "Moderately Aggressive": ["TSLA", "SQ", "SHOP", "ZM", "ROKU", "DOCU", "DDOG", "CRWD", "OKTA", "TTD"],
        "Aggressive": ["NIO", "PLTR", "PLUG", "SPCE", "COIN", "MARA", "RIOT", "MSTR", "ARKK", "ARKG"]
    }
    
    # Select appropriate universe based on risk profile
    if risk_profile in stock_universes:
        universe = stock_universes[risk_profile]
    else:
        universe = stock_universes["Moderate"]  # Default to moderate
    
    # Analyze stocks in the universe
    recommendations = []
    
    for ticker in universe:
        try:
            analysis = st.session_state.chatbot_model.analyze_stock(ticker)
            if analysis and analysis['recommendation'] in ['Strong Buy', 'Buy']:
                # Ensure confidence is a float
                confidence = float(analysis['confidence']) if isinstance(analysis['confidence'], pd.Series) else analysis['confidence']
                recommendations.append({
                    'ticker': ticker,
                    'recommendation': analysis['recommendation'],
                    'confidence': confidence,
                    'reason': str(analysis['reason'])  # Convert reason to string
                })
        except Exception as e:
            st.error(f"Error analyzing {ticker}: {str(e)}")
            continue
    
    # Sort by confidence
    recommendations.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Generate response
    if recommendations:
        response = f"Based on your {risk_profile} risk profile, here are my top stock recommendations:\n\n"
        
        for i, rec in enumerate(recommendations[:3]):  # Top 3 recommendations
            response += f"{i+1}. **{rec['ticker']}**: {rec['recommendation']} (Confidence: {rec['confidence']*100:.1f}%)\n"
            response += f"   *{rec['reason']}*\n\n"
        
        response += "Remember to do your own research before making investment decisions. These recommendations are based on technical analysis and may not account for all factors."
    else:
        response = f"Based on your {risk_profile} risk profile, I don't have strong recommendations at the moment. The market conditions may be uncertain for your risk level. Consider consulting with a financial advisor for personalized advice."
    
    return response

def analyze_specific_stock(ticker):
    """Analyze a specific stock and provide insights"""
    try:
        # Get stock data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1095)
        data = yf.download(ticker, 
                          start=start_date, 
                          end=end_date, 
                          auto_adjust=True)
        
        if data.empty:
            return f"I couldn't find data for {ticker}. Please check the ticker symbol and try again."
        
        # Get company info
        stock = yf.Ticker(ticker)
        info = stock.info
        company_name = info.get('shortName', ticker)
        sector = info.get('sector', 'Unknown')
        industry = info.get('industry', 'Unknown')
        
        # Calculate key metrics
        current_price = float(data['Close'].iloc[-1])
        prev_price = float(data['Close'].iloc[-2])
        price_change = current_price - prev_price
        price_change_pct = (price_change / prev_price) * 100
        
        year_high = data['High'].max()
        year_low = data['Low'].min()
        
        # Get AI analysis
        analysis = st.session_state.chatbot_model.analyze_stock(ticker)
        
        # Generate response
        response = f"## Analysis of {company_name} ({ticker})\n\n"
        response += f"**Sector:** {sector} | **Industry:** {industry}\n\n"
        
        response += f"**Current Price:** ${current_price:.2f}\n"
        response += f"**Daily Change:** {'↑' if price_change >= 0 else '↓'} ${abs(price_change):.2f} ({price_change_pct:.2f}%)\n"
        response += f"**52-Week Range:** ${year_low:.2f} - ${year_high:.2f}\n\n"
        
        response += f"**AI Recommendation:** {analysis['recommendation']}\n"
        response += f"**Confidence:** {analysis['confidence']*100:.1f}%\n"
        response += f"**Reasoning:** {analysis['reason']}\n\n"
        
        response += "**Key Points:**\n"
        
        # Add some fundamental data if available
        pe_ratio = info.get('trailingPE', None)
        if pe_ratio:
            response += f"- P/E Ratio: {pe_ratio:.2f}\n"
        
        market_cap = info.get('marketCap', None)
        if market_cap:
            if market_cap >= 1e12:
                market_cap_str = f"${market_cap/1e12:.2f}T"
            elif market_cap >= 1e9:
                market_cap_str = f"${market_cap/1e9:.2f}B"
            else:
                market_cap_str = f"${market_cap/1e6:.2f}M"
            response += f"- Market Cap: {market_cap_str}\n"
        
        dividend_yield = info.get('dividendYield', None)
        if dividend_yield:
            response += f"- Dividend Yield: {dividend_yield*100:.2f}%\n"
        
        response += "\n**Disclaimer:** This analysis is based on historical data and technical indicators. Always conduct your own research before making investment decisions."
        
        return response
    
    except Exception as e:
        return f"I encountered an error while analyzing {ticker}: {str(e)}. Please try again later."

def provide_portfolio_advice(user_id):
    """Provide portfolio advice based on user's holdings and risk profile"""
    # Get user's risk profile from database
    conn = sqlite3.connect('database/stock_analyzer.db')
    c = conn.cursor()
    
    c.execute("SELECT risk_profile FROM risk_assessments WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
    risk_profile_data = c.fetchone()
    
    if not risk_profile_data:
        conn.close()
        return "I need to understand your risk tolerance before providing portfolio advice. Please complete the Risk Assessment in the Risk Assessment section."
    
    risk_profile = risk_profile_data[0]
    
    # Get user's portfolio from database
    c.execute("""
    SELECT ticker, shares, purchase_price
    FROM portfolio_items
    WHERE user_id = ?
    """, (user_id,))
    
    portfolio_items = c.fetchall()
    conn.close()
    
    if not portfolio_items:
        return "I don't see any stocks in your portfolio yet. Add some stocks to your portfolio, and I'll provide personalized advice."
    
    # Analyze portfolio
    portfolio_data = []
    total_value = 0
    
    for item in portfolio_items:
        ticker, shares, purchase_price = item
        
        try:
            # Get current price
            current_data = yf.download(ticker, period="1d")
            if not current_data.empty:
                current_price = current_data['Close'].iloc[-1]
                
                item_value = shares * current_price
                total_value += item_value
                
                portfolio_data.append({
                    'ticker': ticker,
                    'shares': shares,
                    'value': item_value,
                    'allocation': 0  # Will calculate after total is known
                })
        except:
            continue
    
    # Calculate allocation percentages
    for item in portfolio_data:
        item['allocation'] = (item['value'] / total_value) * 100 if total_value > 0 else 0
    
    # Generate advice based on risk profile and portfolio composition
    response = f"## Portfolio Analysis and Recommendations\n\n"
    
    response += f"Based on your **{risk_profile}** risk profile, here's my analysis of your current portfolio:\n\n"
    
    # Portfolio composition
    response += "**Current Portfolio Allocation:**\n"
    for item in portfolio_data:
        response += f"- {item['ticker']}: ${item['value']:.2f} ({item['allocation']:.1f}%)\n"
    
    response += "\n**Recommendations:**\n"
    
    # Generate recommendations based on risk profile
    if risk_profile == "Conservative":
        response += "- Consider adding more dividend-paying blue-chip stocks for stability\n"
        response += "- Look into adding some bond ETFs like BND or AGG for income\n"
        response += "- Maintain a higher cash position (10-15%) for security\n"
    elif risk_profile == "Moderately Conservative":
        response += "- Balance your portfolio with 60-70% stable blue-chip stocks and 30-40% growth opportunities\n"
        response += "- Consider adding some dividend aristocrats for steady income\n"
        response += "- Explore sector ETFs in healthcare and consumer staples\n"
    elif risk_profile == "Moderate":
        response += "- Aim for a balanced mix of growth and value stocks\n"
        response += "- Consider adding exposure to international markets through ETFs\n"
        response += "- Explore mid-cap stocks with strong fundamentals\n"
    elif risk_profile == "Moderately Aggressive":
        response += "- Increase allocation to growth-oriented sectors like technology and consumer discretionary\n"
        response += "- Consider adding emerging market exposure\n"
        response += "- Look for companies with disruptive potential in established industries\n"
    elif risk_profile == "Aggressive":
        response += "- Focus on high-growth potential stocks in emerging technologies\n"
        response += "- Consider small-cap stocks with strong growth prospects\n"
        response += "- Explore thematic ETFs in areas like clean energy, cybersecurity, or genomics\n"
    
    # Add diversification advice if portfolio is concentrated
    if len(portfolio_data) < 5:
        response += "- Your portfolio appears concentrated. Consider adding more stocks for better diversification\n"
    
    if any(item['allocation'] > 20 for item in portfolio_data):
        response += "- Some positions represent a large percentage of your portfolio. Consider rebalancing to reduce concentration risk\n"
    
    response += "\n**Disclaimer:** These recommendations are based on your risk profile and current holdings. Always conduct your own research before making investment decisions."
    
    return response

def provide_educational_content(query):
    """Provide educational content based on user query"""
    # Dictionary of common investment terms and explanations
    investment_education = {
        "stock": "A stock (also known as equity) represents a share in the ownership of a company. When you buy a stock, you're buying a small piece of that company. As the company grows and earns money, the value of your stock can increase. If the company pays dividends, you'll also receive a portion of the profits.",
        
        "bond": "A bond is a fixed income instrument that represents a loan made by an investor to a borrower (typically corporate or governmental). Bonds are used by companies, municipalities, states, and sovereign governments to finance projects and operations. Bond owners are creditors of the issuer and are entitled to receive interest payments and the return of principal when the bond matures.",
        
        "etf": "An Exchange-Traded Fund (ETF) is a type of investment fund and exchange-traded product, i.e., they are traded on stock exchanges. ETFs are similar to mutual funds, but they trade like stocks throughout the day. ETFs typically track an index, sector, commodity, or other asset, but unlike mutual funds, they can be purchased or sold on a stock exchange the same way as a regular stock.",
        
        "mutual fund": "A mutual fund is an investment vehicle made up of a pool of funds collected from many investors for the purpose of investing in securities such as stocks, bonds, money market instruments, and similar assets. Mutual funds are operated by professional money managers, who allocate the fund's assets and attempt to produce capital gains or income for the fund's investors.",
        
        "dividend": "A dividend is a distribution of a portion of a company's earnings, decided by the board of directors, to a class of its shareholders. Dividends can be issued as cash payments, as shares of stock, or other property. They provide an income stream for investors and signal a company's financial well-being and confidence in future earnings.",
        
        "p/e ratio": "The Price-to-Earnings (P/E) ratio is a valuation ratio of a company's current share price compared to its per-share earnings. It's calculated by dividing the market value per share by the earnings per share. A high P/E ratio could mean that a stock's price is high relative to earnings and possibly overvalued, or that investors are expecting high growth rates in the future.",
        
        "market cap": "Market capitalization (market cap) refers to the total dollar market value of a company's outstanding shares of stock. It's calculated by multiplying the total number of a company's outstanding shares by the current market price of one share. Companies are typically divided into large-cap, mid-cap, and small-cap based on their market capitalization.",
        
        "bull market": "A bull market is a financial market of a group of securities in which prices are rising or are expected to rise. The term is most often used to refer to the stock market but can be applied to anything that is traded, such as bonds, currencies, and commodities. Bull markets are characterized by optimism, investor confidence, and expectations that strong results should continue.",
        
        "bear market": "A bear market is a condition in which securities prices fall 20% or more from recent highs amid widespread pessimism and negative investor sentiment. Bear markets are often associated with declines in an overall market or index like the S&P 500, but individual securities or commodities can also be considered to be in a bear market if they experience a decline of 20% or more over a sustained period.",
        
        "volatility": "Volatility is a statistical measure of the dispersion of returns for a given security or market index. In most cases, the higher the volatility, the riskier the security. Volatility is often measured as either the standard deviation or variance between returns from that same security or market index.",
        
        "diversification": "Diversification is a risk management strategy that mixes a wide variety of investments within a portfolio. The rationale behind this technique is that a portfolio constructed of different kinds of investments will, on average, yield higher long-term returns and lower the risk of any individual holding or security.",
        
        "asset allocation": "Asset allocation is an investment strategy that aims to balance risk and reward by apportioning a portfolio's assets according to an individual's goals, risk tolerance, and investment horizon. The three main asset classes - equities, fixed-income, and cash and equivalents - have different levels of risk and return, so each will behave differently over time.",
        
        "roth ira": "A Roth IRA is an individual retirement account that offers tax-free growth and tax-free withdrawals in retirement. Roth IRA contributions are made with after-tax dollars, meaning you pay taxes on the money before it goes into the account. In retirement, you can withdraw your contributions and earnings tax-free, provided you meet certain conditions.",
        
        "401k": "A 401(k) is a tax-advantaged, defined-contribution retirement account offered by many employers to their employees. It is named after a section of the U.S. Internal Revenue Code. Workers can make contributions to their 401(k) accounts through automatic payroll withholding, and their employers can match some or all of those contributions."
    }
    
    # Check for educational keywords in the query
    for term, explanation in investment_education.items():
        if term in query.lower():
            return f"**{term.upper()}**: {explanation}"
    
    # If no specific term is found, provide a general response
    return "I can provide information about various investment concepts like stocks, bonds, ETFs, mutual funds, dividends, P/E ratios, market capitalization, bull markets, bear markets, volatility, diversification, asset allocation, Roth IRAs, and 401(k)s. Please ask about a specific term you'd like to learn more about."
