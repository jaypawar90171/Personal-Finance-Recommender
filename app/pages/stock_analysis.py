import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
from utils.stock_utils import get_company_logo, get_stock_news
from utils.stock_analyzer import StockAnalyzer

def show_stock_analysis(user_id):
    st.markdown("""
    <style>
    .news-card {
        background: #181b20;
        border: 1px solid #e6e6e6;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .news-header h4 {
        margin: 0 0 0.5rem 0;
        color: #1E88E5;
        font-size: 1.1rem;
    }
    .news-meta {
        color: #666;
        font-size: 0.8rem;
    }
    .news-card p {
        margin: 0.8rem 0;
        color: white;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    .news-footer {
        margin-top: 0.8rem;
        text-align: right;
    }
    .news-footer a {
        color: white;
        text-decoration: none;
        font-size: 0.9rem;
        font-weight: 500;
    }
    .news-footer a:hover {
        text-decoration: underline;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header">Stock Analysis</div>', unsafe_allow_html=True)
    
    # Initialize analyzer if not already done
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = StockAnalyzer()
    
    # Get user's selected stocks from database
    conn = sqlite3.connect('database/stock_analyzer.db')
    c = conn.cursor()
    
    c.execute("SELECT ticker FROM selected_stocks WHERE user_id = ?", (user_id,))
    selected_stocks_db = [row[0] for row in c.fetchall()]
    
    # Initialize selected_stocks in session state if not already done
    if 'selected_stocks' not in st.session_state:
        st.session_state.selected_stocks = selected_stocks_db if selected_stocks_db else []
    
    # Stock selection
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        ticker_input = st.text_input("Enter Stock Ticker", value="AAPL" if not st.session_state.selected_stocks else st.session_state.selected_stocks[0])
    
    with col2:
        start_date = st.date_input(
            "Start Date", 
            datetime.now() - timedelta(days=365),  # Default to 1 year
            max_value=datetime.now() - timedelta(days=1)
        )
    
    with col3:
        end_date = st.date_input(
            "End Date",
            datetime.now(),
            min_value=start_date,
            max_value=datetime.now()
        )
    
    # Add button to add stock to analysis
    col1, col2 = st.columns([3, 1])
    
    with col1:
        compare_mode = st.checkbox("Compare Multiple Stocks", value=len(st.session_state.selected_stocks) > 1)
    
    with col2:
        if st.button("Add to Analysis"):
            ticker = ticker_input.strip().upper()
            if ticker and ticker not in st.session_state.selected_stocks:
                # Validate ticker
                try:
                    stock_data = yf.download(ticker, period="1d")
                    
                    if stock_data.empty:
                        st.error(f"No data found for ticker {ticker}")
                    else:
                        # Add to session state
                        st.session_state.selected_stocks.append(ticker)
                        
                        # Add to database
                        c.execute("INSERT OR IGNORE INTO selected_stocks (user_id, ticker) VALUES (?, ?)", (user_id, ticker))
                        conn.commit()
                        
                        st.success(f"Added {ticker} to analysis!")
                        st.experimental_rerun()
                except:
                    print(f"Error adding {ticker} to analysis.")
                    # st.error(f"Error adding {ticker} to analysis.")
    
    # Display selected stocks for comparison
    if compare_mode and st.session_state.selected_stocks:
        st.markdown('<div class="sub-header">Selected Stocks</div>', unsafe_allow_html=True)
        
        selected_tickers = st.multiselect(
            "Select stocks to analyze",
            options=st.session_state.selected_stocks,
            default=st.session_state.selected_stocks
        )
        
        if st.button("Remove Selected"):
            for ticker in selected_tickers:
                if ticker in st.session_state.selected_stocks:
                    st.session_state.selected_stocks.remove(ticker)
                    
                    # Remove from database
                    c.execute("DELETE FROM selected_stocks WHERE user_id = ? AND ticker = ?", (user_id, ticker))
            
            conn.commit()
            st.success("Removed selected stocks from analysis!")
            st.rerun()
        
        if not st.session_state.selected_stocks:
            st.warning("Please add stocks to analyze.")
            conn.close()
            return
    else:
        # Single stock mode
        if ticker_input:
            selected_tickers = [ticker_input.strip().upper()]
        else:
            st.warning("Please enter a stock ticker.")
            conn.close()
            return
    
    conn.close()
    
    # Fetch data and perform analysis
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Fetch benchmark data (S&P 500)
    benchmark_data = st.session_state.analyzer.fetch_stock_data('^GSPC', start_date_str, end_date_str)
    benchmark_data = st.session_state.analyzer.calculate_technical_indicators(benchmark_data)
    
    # Fetch and analyze selected stocks
    tickers_data = {}
    tickers_risk_metrics = {}
    tickers_fundamentals = {}
    
    for ticker in selected_tickers:
        with st.spinner(f"Analyzing {ticker}..."):
            # Fetch stock data
            data = st.session_state.analyzer.fetch_stock_data(ticker, start_date_str, end_date_str)
            
            if data is None or data.empty:
                st.error(f"No data available for {ticker}. Please check the ticker symbol and date range.")
                continue
            
            # Calculate technical indicators
            data = st.session_state.analyzer.calculate_technical_indicators(data)
            
            # Calculate risk metrics
            risk_metrics = st.session_state.analyzer.calculate_risk_metrics(data, benchmark_data)
            
            # Fetch fundamental data
            fundamentals = st.session_state.analyzer.fetch_fundamental_data(ticker)
            
            # Store data for comparison
            tickers_data[ticker] = data
            tickers_risk_metrics[ticker] = risk_metrics
            tickers_fundamentals[ticker] = fundamentals
    
    if not tickers_data:
        st.error("No valid data available for the selected stocks. Please check your inputs and try again.")
        return
    
    # Display analysis
    if compare_mode:
        # Comparative analysis
        st.markdown('<div class="sub-header">Comparative Analysis</div>', unsafe_allow_html=True)
        
        # Comparative performance chart
        fig_comp = create_comparative_chart(tickers_data, benchmark_data)
        st.plotly_chart(fig_comp, use_container_width=True)
        
        # Risk-return scatter plot
        risk_return_plot = create_risk_return_plot(tickers_risk_metrics, tickers_data)
        if risk_return_plot:
            st.plotly_chart(risk_return_plot, use_container_width=True)
        
        # Correlation heatmap
        fig_corr = create_correlation_heatmap(tickers_data)
        st.plotly_chart(fig_corr, use_container_width=True)
        
        # Comparative metrics table
        st.markdown('<div class="sub-header">Comparative Metrics</div>', unsafe_allow_html=True)
        
        comparison_data = []
        
        for ticker, data in tickers_data.items():
            if data is None or data.empty:
                continue
            
            current_price = data['Close'].iloc[-1]
            ytd_return = (data['Close'].iloc[-1] / data['Close'].iloc[0] - 1) * 100
            volatility = tickers_risk_metrics[ticker]['Volatility (Annual)'] * 100
            sharpe = tickers_risk_metrics[ticker]['Sharpe Ratio (Annual)']
            beta = tickers_risk_metrics[ticker].get('Beta', np.nan)
            
            print(f"Current Price: {current_price}, YTD Return: {ytd_return}, Volatility: {volatility}, Sharpe: {sharpe}, Beta: {beta}")    

            comparison_data.append({
                'Ticker': ticker,
                'Current Price': f"${float(current_price[0]):.2f}",
                'YTD Return (%)': f"{float(ytd_return[0]):.2f}%",
                'Volatility (%)': f"{volatility:.2f}%",
                'Sharpe Ratio': f"{sharpe:.2f}",
                'Beta': f"{beta:.2f}" if not np.isnan(beta) else "N/A"
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)
        
    else:
        # Single stock analysis
        ticker = selected_tickers[0]
        data = tickers_data[ticker]
        risk_metrics = tickers_risk_metrics[ticker]
        fundamentals = tickers_fundamentals[ticker]
        
        # Stock header with logo
        col1, col2 = st.columns([1, 3])
        
        with col1:
            logo_url = get_company_logo(ticker)
            st.image(logo_url, width=80)
        
        with col2:
            company_name = fundamentals.get('shortName', ticker) if 'shortName' in fundamentals else ticker
            sector = fundamentals.get('sector', 'N/A')
            industry = fundamentals.get('industry', 'N/A')
            
            st.markdown(f"<h1>{company_name} ({ticker})</h1>", unsafe_allow_html=True)
            st.markdown(f"<p>Sector: {sector} | Industry: {industry}</p>", unsafe_allow_html=True)
        
        # Price and key metrics
        current_price = data['Close'].iloc[-1]
        prev_price = data['Close'].iloc[-2]
        price_change = current_price - prev_price
        price_change_pct = (price_change / prev_price) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">${float(current_price.iloc[0]):.2f}</div>
                <div class="metric-label">Current Price</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            change_color = "positive" if float(price_change.iloc[-1]) >= 0 else "negative"
            change_icon = "↑" if float(price_change.iloc[-1]) >= 0  else "↓"
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value {change_color}">{change_icon} ${abs(float(price_change)):.2f} ({float(price_change_pct):.2f}%)</div>
                <div class="metric-label">Daily Change% ({float(price_change_pct):.2f}%)</div>
                <div class="metric-label">Daily Change</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            ytd_return = (data['Close'].iloc[-1] / data['Close'].iloc[0] - 1) * 100
            ytd_color = "positive" if ytd_return.any() else "negative"
            ytd_icon = "↑" if ytd_return.any() else "↓"
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value {ytd_color}">{ytd_icon} {abs(float(ytd_return)):.0f}%</div>
                <div class="metric-label">Period Return</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            volume = data['Volume'].iloc[-1]
            print(volume[0])
            # avg_volume = data['Volume'].mean()
            # volume_change = (volume / avg_volume - 1) * 100
            volume_color = "positive" #if volume >= avg_volume else "neutral"
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value {volume_color}">{volume[0]:,.0f}</div>
                <div class="metric-label">Volume ({volume[0]:.2f}% vs Avg)</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Tabs for different analyses
        tabs = st.tabs(["Price Chart", "Technical Indicators", "Fundamentals", "Risk Analysis", "News"])
        
        with tabs[0]:
            # Price chart
            fig_price = create_candlestick_chart(data, ticker)
            st.plotly_chart(fig_price, use_container_width=True)
            
            # Returns chart
            fig_returns = create_returns_chart(data)
            st.plotly_chart(fig_returns, use_container_width=True)
        
        with tabs[1]:
            # Technical indicators
            col1, col2 = st.columns(2)
            
            with col1:
                fig_rsi = create_technical_chart(data, 'RSI')
                st.plotly_chart(fig_rsi, use_container_width=True)
                
                fig_bb = create_technical_chart(data, 'Bollinger')
                st.plotly_chart(fig_bb, use_container_width=True)
            
            with col2:
                fig_macd = create_technical_chart(data, 'MACD')
                st.plotly_chart(fig_macd, use_container_width=True)
                
                # Volume analysis
                fig_vol = go.Figure()
                
                fig_vol.add_trace(go.Bar(
                    x=data.index,
                    y=data['Volume'],
                    name='Volume',
                    marker_color='rgba(100, 181, 246, 0.5)'
                ))
                
                fig_vol.add_trace(go.Scatter(
                    x=data.index,
                    y=data['Volume_MA50'],
                    name='50-Day Volume MA',
                    line=dict(color='#FF9800', width=2)
                ))
                
                fig_vol.update_layout(
                    title='Volume Analysis',
                    xaxis_title='Date',
                    yaxis_title='Volume',
                    height=300,
                    margin=dict(l=50, r=50, t=80, b=50),
                )
                
                st.plotly_chart(fig_vol, use_container_width=True)
            
            # Technical summary
            st.markdown('<div class="sub-header">Technical Summary</div>', unsafe_allow_html=True)
            
            # Moving Averages
            ma50 = data['MA50'].iloc[-1]
            ma200 = data['MA200'].iloc[-1]
            ma_signal = "BULLISH" if ma50 > ma200 else "BEARISH"
            ma_distance = (current_price / ma200 - 1) * 100
            
            # RSI
            rsi = data['RSI'].iloc[-1]
            if rsi > 70:
                rsi_signal = "OVERBOUGHT"
            elif rsi < 30:
                rsi_signal = "OVERSOLD"
            else:
                rsi_signal = "NEUTRAL"
            
            # MACD
            macd = data['MACD'].iloc[-1]
            signal = data['Signal_Line'].iloc[-1]
            histogram = data['MACD_Histogram'].iloc[-1]
            
            if macd > signal and histogram > 0:
                macd_signal = "BULLISH"
            elif macd < signal and histogram < 0:
                macd_signal = "BEARISH"
            else:
                macd_signal = "NEUTRAL"
            
            # Bollinger Bands
            upper_band = data['Upper_Band'].iloc[-1]
            lower_band = data['Lower_Band'].iloc[-1]
            print(current_price[0], upper_band, lower_band)
            if current_price[0] > upper_band:
                bb_signal = "OVERBOUGHT"
            elif current_price[0] < lower_band:
                bb_signal = "OVERSOLD"
            else:
                bb_signal = "NEUTRAL"
            
            # Display technical signals
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                ma_color = "positive" if ma_signal == "BULLISH" else "negative"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value {ma_color}">{ma_signal}</div>
                    <div class="metric-label">Moving Averages</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                rsi_color = "negative" if rsi_signal == "OVERBOUGHT" else "positive" if rsi_signal == "OVERSOLD" else "neutral"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value {rsi_color}">{rsi_signal}</div>
                    <div class="metric-label">RSI ({rsi:.2f})</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                macd_color = "positive" if macd_signal == "BULLISH" else "negative" if macd_signal == "BEARISH" else "neutral"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value {macd_color}">{macd_signal}</div>
                    <div class="metric-label">MACD</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                bb_color = "negative" if bb_signal == "OVERBOUGHT" else "positive" if bb_signal == "OVERSOLD" else "neutral"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value {bb_color}">{bb_signal}</div>
                    <div class="metric-label">Bollinger Bands</div>
                </div>
                """, unsafe_allow_html=True)
        
        with tabs[2]:
            # Fundamental analysis
            if fundamentals:
                # Key financial metrics
                st.markdown('<div class="sub-header">Key Financial Metrics</div>', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    market_cap = fundamentals.get('Market Cap', 'N/A')
                    pe_ratio = fundamentals.get('P/E Ratio', 'N/A')
                    forward_pe = fundamentals.get('Forward P/E', 'N/A')
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{market_cap}</div>
                        <div class="metric-label">Market Cap</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{pe_ratio}</div>
                        <div class="metric-label">P/E Ratio</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{forward_pe}</div>
                        <div class="metric-label">Forward P/E</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    eps = fundamentals.get('EPS', 'N/A')
                    dividend_yield = fundamentals.get('Dividend Yield (%)', 'N/A')
                    peg_ratio = fundamentals.get('PEG Ratio', 'N/A')
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{eps}</div>
                        <div class="metric-label">EPS</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{dividend_yield}</div>
                        <div class="metric-label">Dividend Yield (%)</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{peg_ratio}</div>
                        <div class="metric-label">PEG Ratio</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    profit_margin = fundamentals.get('Profit Margin', 'N/A')
                    roe = fundamentals.get('ROE', 'N/A')
                    debt_to_equity = fundamentals.get('Debt to Equity', 'N/A')
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{profit_margin}</div>
                        <div class="metric-label">Profit Margin (%)</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{roe}</div>
                        <div class="metric-label">Return on Equity (%)</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{debt_to_equity}</div>
                        <div class="metric-label">Debt to Equity</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Business summary
                st.markdown('<div class="sub-header">Business Summary</div>', unsafe_allow_html=True)
                
                business_summary = fundamentals.get('Business Summary', 'No business summary available.')
                st.markdown(f"<div class='card'>{business_summary}</div>", unsafe_allow_html=True)
            else:
                st.info("Fundamental data not available for this stock.")
        
        with tabs[3]:
            # Risk analysis
            st.markdown('<div class="sub-header">Risk Metrics</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Volatility
                daily_vol = risk_metrics.get('Volatility (Daily)', 0) * 100
                annual_vol = risk_metrics.get('Volatility (Annual)', 0) * 100
                
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{annual_vol:.2f}%</div>
                    <div class="metric-label">Annual Volatility</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Beta
                beta = risk_metrics.get('Beta', np.nan)
                beta_value = f"{beta:.2f}" if not np.isnan(beta) else "N/A"
                
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{beta_value}</div>
                    <div class="metric-label">Beta (vs S&P 500)</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Max Drawdown
                max_dd = risk_metrics.get('Max Drawdown', 0) * 100
                
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value negative">{max_dd:.2f}%</div>
                    <div class="metric-label">Maximum Drawdown</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Sharpe Ratio
                sharpe = risk_metrics.get('Sharpe Ratio (Annual)', 0)
                sharpe_color = "positive" if sharpe > 1 else "neutral" if sharpe > 0 else "negative"
                
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value {sharpe_color}">{sharpe:.2f}</div>
                    <div class="metric-label">Sharpe Ratio (Annual)</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Sortino Ratio
                sortino = risk_metrics.get('Sortino Ratio (Annual)', 0)
                sortino_color = "positive" if sortino > 1 else "neutral" if sortino > 0 else "negative"
                
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value {sortino_color}">{sortino:.2f}</div>
                    <div class="metric-label">Sortino Ratio (Annual)</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Alpha
                alpha = risk_metrics.get('Alpha', 0)
                alpha_color = "positive" if alpha > 0 else "negative"
                
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value {alpha_color}">{alpha:.4f}</div>
                    <div class="metric-label">Alpha (Jensen's Alpha)</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Get user's risk profile from database
            conn = sqlite3.connect('database/stock_analyzer.db')
            c = conn.cursor()
            c.execute("SELECT risk_score, risk_profile FROM risk_assessments WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
            risk_data = c.fetchone()
            conn.close()
            
            # Risk assessment
            if risk_data:
                st.markdown('<div class="sub-header">Risk Assessment</div>', unsafe_allow_html=True)
                
                # Evaluate stock suitability
                risk_tolerance = {
                    "score": risk_data[0],
                    "profile": risk_data[1]
                }
                
                suitability = st.session_state.analyzer.evaluate_stock_suitability(ticker, risk_metrics, risk_tolerance)
                
                if suitability:
                    # Overall suitability score
                    score = suitability['Overall Suitability Score']
                    match_rating = suitability['Match Rating']
                    match_description = suitability['Match Description']
                    
                    score_color = "positive" if match_rating == "Excellent Match" else "neutral" if match_rating == "Good Match" else "negative"
                    
                    st.markdown(f"""
                    <div class="card">
                        <h3>Suitability Score: <span class="{score_color}">{score:.2f}/100</span></h3>
                        <h4>{match_rating}</h4>
                        <p>{match_description}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Risk factor breakdown
                    st.markdown('<h4>Risk Factor Breakdown</h4>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Volatility
                        vol_rating = suitability['Volatility']['Rating']
                        vol_score = suitability['Volatility']['Score']
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{vol_rating}</div>
                            <div class="metric-label">Volatility (Score: {vol_score})</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Beta
                        beta_rating = suitability['Beta']['Rating']
                        beta_score = suitability['Beta']['Score']
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{beta_rating}</div>
                            <div class="metric-label">Beta (Score: {beta_score})</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # Sharpe Ratio
                        sharpe_rating = suitability['Sharpe Ratio']['Rating']
                        sharpe_score = suitability['Sharpe Ratio']['Score']
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{sharpe_rating}</div>
                            <div class="metric-label">Sharpe Ratio (Score: {sharpe_score})</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Max Drawdown
                        dd_rating = suitability['Max Drawdown']['Rating']
                        dd_score = suitability['Max Drawdown']['Score']
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{dd_rating}</div>
                            <div class="metric-label">Max Drawdown (Score: {dd_score})</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Unable to assess stock suitability.")
            else:
                st.info("Complete the risk tolerance assessment to see if this stock matches your risk profile.")
                
                if st.button("Go to Risk Assessment"):
                    st.session_state.page = "Risk Assessment"
                    st.experimental_rerun()
        
        with tabs[4]:
            # News
            st.markdown('<div class="sub-header">Recent News</div>', unsafe_allow_html=True)
            
            news = get_stock_news(ticker)
            
            if news:
                for item in news:
                    # Handle news items with proper error checking
                    try:
                        title = item.get('title', 'No title available')
                        publisher = item.get('publisher', 'Unknown source')
                        link = item.get('link', '#')
                        published = item.get('published', 'Unknown date')
                        summary = item.get('summary', 'No summary available')

                        st.markdown(f"""
                        <div class="news-card">
                            <div class="news-header">
                                <h4>{title}</h4>
                                <span class="news-meta">{publisher} • {published}</span>
                            </div>
                            <p>{summary[:200]}...</p>
                            <div class="news-footer">
                                <a href="{link}" target="_blank" rel="noopener noreferrer">Read more →</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        print(f"Error displaying news item: {str(e)}")
                        continue
            else:
                st.info("No recent news available for this stock.")

            # Add some spacing
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Actions
        st.markdown('<div class="sub-header">Actions</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Add to Portfolio"):
                # Check if already in portfolio
                conn = sqlite3.connect('database/stock_analyzer.db')
                c = conn.cursor()
                c.execute("SELECT id FROM portfolio_items WHERE user_id = ? AND ticker = ?", (user_id, ticker))
                existing = c.fetchone()
                
                if existing:
                    st.info(f"{ticker} is already in your portfolio.")
                else:
                    # Redirect to portfolio page
                    st.session_state.add_to_portfolio = ticker
                    st.session_state.page = "Portfolio"
                    st.experimental_rerun()
                
                conn.close()
        
        with col2:
            if st.button("Add to Watchlist"):
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
                    st.success(f"Added {ticker} to your watchlist!")
                
                conn.close()
        
        with col3:
            if st.button("Download Data"):
                csv = data.to_csv().encode('utf-8')
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{ticker}_data.csv",
                    mime="text/csv"
                )

# Helper functions for charts
def create_candlestick_chart(data, ticker):
    fig = go.Figure()

    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price',
        increasing_line_color='#26A69A',
        decreasing_line_color='#EF5350'
    ))

    # Add volume as bar chart at the bottom
    fig.add_trace(go.Bar(
        x=data.index,
        y=data['Volume'],
        name='Volume',
        marker_color='rgba(100, 181, 246, 0.5)',
        yaxis='y2'
    ))

    # Add moving averages
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['MA50'],
        name='50-Day MA',
        line=dict(color='#FF9800', width=1.5)
    ))

    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['MA200'],
        name='200-Day MA',
        line=dict(color='#F06292', width=1.5)
    ))

    # Update layout
    fig.update_layout(
        title=f'{ticker} Stock Price',
        xaxis_title='Date',
        yaxis_title='Price ($)',
        xaxis_rangeslider_visible=False,
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right',
            showgrid=False,
            range=[0, data['Volume'].max() * 5]
        ),
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50),
        plot_bgcolor='#0e1117',
        paper_bgcolor='#0e1117',
    )

    return fig

def create_technical_chart(data, indicator):
    fig = go.Figure()

    if indicator == 'RSI':
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['RSI'],
            name='RSI',
            line=dict(color='#7B1FA2', width=2)
        ))
        
        # Add overbought/oversold lines
        fig.add_shape(
            type="line",
            x0=data.index[0],
            y0=70,
            x1=data.index[-1],
            y1=70,
            line=dict(color="#EF5350", width=1.5, dash="dash"),
        )
        
        fig.add_shape(
            type="line",
            x0=data.index[0],
            y0=30,
            x1=data.index[-1],
            y1=30,
            line=dict(color="#26A69A", width=1.5, dash="dash"),
        )
        
        fig.update_layout(
            title='Relative Strength Index (RSI)',
            yaxis_title='RSI',
            yaxis=dict(range=[0, 100]),
            height=300,
            margin=dict(l=50, r=50, t=80, b=50),
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117',
        )
        
    elif indicator == 'MACD':
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['MACD'],
            name='MACD',
            line=dict(color='#42A5F5', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Signal_Line'],
            name='Signal Line',
            line=dict(color='#FF7043', width=2)
        ))
        
        colors = ['#26A69A' if val >= 0 else '#EF5350' for val in data['MACD_Histogram']]
        
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['MACD_Histogram'],
            name='Histogram',
            marker_color=colors
        ))
        
        fig.update_layout(
            title='MACD (12-26-9)',
            yaxis_title='MACD',
            height=300,
            margin=dict(l=50, r=50, t=80, b=50),
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117',
        )
        
    elif indicator == 'Bollinger':
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Close'],
            name='Close Price',
            line=dict(color='#1E88E5', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['MA20'],
            name='20-Day MA',
            line=dict(color='#FFA000', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Upper_Band'],
            name='Upper Band',
            line=dict(color='#26A69A', width=1.5, dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Lower_Band'],
            name='Lower Band',
            line=dict(color='#EF5350', width=1.5, dash='dash')
        ))
        
        fig.update_layout(
            title='Bollinger Bands (20-Day, 2 STD)',
            yaxis_title='Price ($)',
            height=300,
            margin=dict(l=50, r=50, t=80, b=50),
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117',
        )
        
    return fig

def create_returns_chart(data):
    # Calculate cumulative return
    if 'Daily_Return' not in data.columns:
        data['Daily_Return'] = data['Close'].pct_change()
    
    cumulative_return = (1 + data['Daily_Return']).cumprod() - 1

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data.index,
        y=cumulative_return * 100,  # Convert to percentage
        name='Cumulative Return',
        line=dict(color='#1E88E5', width=2),
        fill='tozeroy',
        fillcolor='rgba(30, 136, 229, 0.1)'
    ))

    fig.update_layout(
        title='Cumulative Returns',
        yaxis_title='Return (%)',
        height=300,
        margin=dict(l=50, r=50, t=80, b=50),
        plot_bgcolor='#0e1117',
        paper_bgcolor='#0e1117',
    )

    return fig

def create_correlation_heatmap(tickers_data):
    # Prepare returns data for correlation
    returns_data = {}

    for ticker, data in tickers_data.items():
        if data is not None and not data.empty:
            # Process data to handle DatetimeIndex
            if isinstance(data.index, pd.DatetimeIndex):
                data = data.copy()  # Create a copy to avoid modifying original data
            
            # Calculate daily returns
            if 'Daily_Return' not in data.columns:
                data['Daily_Return'] = data['Close'].pct_change()
            
            # Ensure we're working with a Series, not a DataFrame
            if isinstance(data['Daily_Return'], pd.DataFrame):
                returns_data[ticker] = data['Daily_Return'].squeeze()
            else:
                returns_data[ticker] = data['Daily_Return']

    # Check if we have any data to process
    if not returns_data:
        return None

    # Create a DataFrame with all returns and align indices
    returns_df = pd.DataFrame(returns_data)
    returns_df = returns_df.dropna()

    # Check if we have enough data to create correlation matrix
    if returns_df.empty or len(returns_df.columns) < 2:
        return None

    # Calculate correlation matrix
    corr_matrix = returns_df.corr()

    # Create heatmap
    fig = px.imshow(
        corr_matrix,
        text_auto='.2f',
        color_continuous_scale='RdBu_r',
        zmin=-1,
        zmax=1,
        aspect="auto"
    )

    fig.update_layout(
        title='Correlation Matrix of Daily Returns',
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        plot_bgcolor='#0e1117',
        paper_bgcolor='#0e1117',
    )

    return fig

def create_comparative_chart(tickers_data, benchmark_data=None):
    fig = go.Figure()

    # Ensure we have enough data points
    for ticker, data in tickers_data.items():
        if data is not None and not data.empty:
            # Calculate daily returns and normalized prices
            data = data.copy()  # Create a copy to avoid modifying original data
            data['Normalized'] = (data['Close'] / data['Close'].iloc[0]) * 100
            
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['Normalized'],
                name=ticker,
                mode='lines',  # Explicitly set mode to 'lines'
                line=dict(width=2)
            ))

    # Add benchmark comparison if available
    if benchmark_data is not None and not benchmark_data.empty:
        benchmark_data = benchmark_data.copy()
        benchmark_data['Normalized'] = (benchmark_data['Close'] / benchmark_data['Close'].iloc[0]) * 100
        
        fig.add_trace(go.Scatter(
            x=benchmark_data.index,
            y=benchmark_data['Normalized'],
            name='S&P 500',
            mode='lines',  # Explicitly set mode to 'lines'
            line=dict(color='black', width=2, dash='dash')
        ))

    fig.update_layout(
        title='Comparative Performance (Base = 100)',
        xaxis_title='Date',
        yaxis_title='Normalized Price',
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified',
        plot_bgcolor='#0e1117',
        paper_bgcolor='#0e1117',
    )

    # Update x-axis to show proper date range
    fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )

    return fig

def create_risk_return_plot(tickers_risk_metrics, tickers_data):
    risk_return_data = []

    for ticker, risk_metrics in tickers_risk_metrics.items():
        if ticker in tickers_data and tickers_data[ticker] is not None:
            data = tickers_data[ticker]
            
            # Convert Series to float values safely
            try:
                # Handle Series properly for Close prices
                if isinstance(data['Close'].iloc[0], pd.Series):
                    close_start = float(data['Close'].iloc[0].iloc[0])
                    close_end = float(data['Close'].iloc[-1].iloc[0])
                else:
                    close_start = float(data['Close'].iloc[0])
                    close_end = float(data['Close'].iloc[-1])
                
                # Calculate metrics
                annual_return = (close_end / close_start - 1) * 100
                annual_volatility = float(risk_metrics['Volatility (Annual)'] * 100)
                sharpe = float(risk_metrics['Sharpe Ratio (Annual)'])
                
                risk_return_data.append({
                    'Ticker': ticker,
                    'Annual Return (%)': annual_return,
                    'Annual Volatility (%)': annual_volatility,
                    'Sharpe Ratio': sharpe
                })
            except Exception as e:
                print(f"Error processing {ticker}: {str(e)}")
                continue

    if not risk_return_data:
        return None

    df = pd.DataFrame(risk_return_data)
    
    if df.empty:
        return None

    try:
        # Optionally scale Sharpe Ratio for larger bubbles
        df['Bubble Size'] = df['Sharpe Ratio'] * 100  # Increase factor as needed

        fig = px.scatter(
            df,
            x='Annual Volatility (%)',
            y='Annual Return (%)',
            text='Ticker',
            size='Bubble Size',           # Use the scaled size
            size_max=80,                  # Increase max bubble size
            color='Sharpe Ratio',
            color_continuous_scale='RdYlGn'
        )

        fig.update_traces(
            textposition='top center',
            marker=dict(
                line=dict(width=1, color='DarkSlateGrey'),
                sizeref=0.5,
                sizemode='area'
            ),
            textfont=dict(color='white')  # <-- Add this line for white text
        )

        fig.update_layout(
            title='Risk-Return Analysis',
            xaxis_title='Risk (Annual Volatility %)',
            yaxis_title='Return (Annual %)',
            height=500,
            showlegend=True,
            margin=dict(l=50, r=50, t=80, b=50),
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117',
            hovermode='closest'
        )

        # Add gridlines
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

        return fig
    except Exception as e:
        print(f"Error creating plot: {str(e)}")
        return None
