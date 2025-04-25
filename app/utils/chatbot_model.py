import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import re
import random

class StockChatbotModel:
    def __init__(self):
        """Initialize the improved chatbot model without heavy training"""
        self.stock_data_cache = {}
        self.market_sentiment = self._get_market_sentiment()
        self.popular_stocks = {
            'tech': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA'],
            'finance': ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'V', 'MA'],
            'healthcare': ['JNJ', 'PFE', 'MRK', 'ABBV', 'UNH', 'CVS', 'ABT'],
            'consumer': ['PG', 'KO', 'PEP', 'WMT', 'MCD', 'SBUX', 'NKE'],
            'industrial': ['GE', 'BA', 'CAT', 'MMM', 'HON', 'UPS', 'FDX'],
            'energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'PSX', 'VLO'],
            'dividend': ['T', 'VZ', 'MO', 'PM', 'O', 'XOM', 'JNJ'],
            'growth': ['TSLA', 'NVDA', 'SHOP', 'SQ', 'ROKU', 'DDOG', 'NET']
        }
        print("Chatbot model initialized successfully!")
    
    def _get_market_sentiment(self):
        """Get overall market sentiment based on major indices"""
        try:
            # Get S&P 500 data for the last week
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            sp500 = yf.download('^GSPC', start=start_date, end=end_date)
            
            if sp500.empty:
                return "neutral"
            
            # Calculate weekly change
            weekly_change = (sp500['Close'].iloc[-1] / sp500['Close'].iloc[0] - 1) * 100
            
            if weekly_change > 2:
                return "bullish"
            elif weekly_change < -2:
                return "bearish"
            else:
                return "neutral"
        except:
            return "neutral"
    
    def analyze_stock(self, ticker):
        """Analyze a stock and return recommendation with error handling"""
        try:
            # Check cache first
            if ticker in self.stock_data_cache and (datetime.now() - self.stock_data_cache[ticker]['timestamp']).seconds < 3600:
                return self.stock_data_cache[ticker]['analysis']
            
            # Get recent data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)  # Use 6 months of data
            data = yf.download(ticker, start=start_date, end=end_date)
            
            if data.empty or len(data) < 30:
                return {
                    'recommendation': 'Neutral',
                    'confidence': 0.5,
                    'reason': 'Not enough historical data available for analysis'
                }
            
            # Get stock info
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Calculate technical indicators
            data = self._calculate_indicators(data)
            
            # Generate recommendation based on technical indicators
            recommendation, confidence, reason = self._generate_recommendation(data, ticker, info)
            
            # Cache the result
            analysis = {
                'recommendation': recommendation,
                'confidence': confidence,
                'reason': reason
            }
            
            self.stock_data_cache[ticker] = {
                'timestamp': datetime.now(),
                'analysis': analysis
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing {ticker}: {str(e)}")
            return {
                'recommendation': 'Error',
                'confidence': 0,
                'reason': f"Error analyzing stock: {str(e)}"
            }
    
    def _calculate_indicators(self, data):
        """Calculate technical indicators for stock analysis"""
        # RSI
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        # Align gain and loss to data's index
        gain, loss = gain.align(data.index, axis=0, fill_value=np.nan)
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # Moving Averages
        data['MA50'] = data['Close'].rolling(window=50).mean()
        data['MA200'] = data['Close'].rolling(window=200).mean()
        data['MA_Signal'] = (data['MA50'] > data['MA200']).astype(int)

        # MACD
        data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
        data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = data['EMA12'] - data['EMA26']
        data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()

        # Bollinger Bands
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['STD20'] = data['Close'].rolling(window=20).std()
        data['Upper_Band'] = data['MA20'] + (data['STD20'] * 2)
        data['Lower_Band'] = data['MA20'] - (data['STD20'] * 2)

        # BB Signal
        data['BB_Signal'] = 0
        # Use .loc with index alignment
        data.loc[data['Close'] > data['Upper_Band'], 'BB_Signal'] = -1  # Overbought
        data.loc[data['Close'] < data['Lower_Band'], 'BB_Signal'] = 1   # Oversold

        # Volume Signal
        data['Volume_MA50'] = data['Volume'].rolling(window=50).mean()
        data['Volume_Signal'] = (data['Volume'] > data['Volume_MA50']).astype(int)

        return data
    
    def _generate_recommendation(self, data, ticker, info):
        """Generate stock recommendation based on technical analysis"""
        # Get latest values
        latest = data.iloc[-1]
        
        # Initialize scores
        buy_signals = 0
        sell_signals = 0
        total_signals = 5
        
        # RSI signal
        if latest['RSI'] < 30:
            buy_signals += 1
        elif latest['RSI'] > 70:
            sell_signals += 1
        
        # Moving Average signal
        if latest['MA50'] > latest['MA200']:
            buy_signals += 1
        else:
            sell_signals += 1
        
        # MACD signal
        if latest['MACD'] > latest['Signal_Line']:
            buy_signals += 1
        else:
            sell_signals += 1
        
        # Bollinger Bands signal
        if latest['BB_Signal'] == 1:
            buy_signals += 1
        elif latest['BB_Signal'] == -1:
            sell_signals += 1
        
        # Volume signal
        if latest['Volume_Signal'] == 1:
            buy_signals += 1
        
        # Calculate confidence
        confidence = buy_signals / total_signals
        
        # Determine recommendation
        if confidence > 0.7:
            recommendation = 'Strong Buy'
            reason = f"Technical indicators are strongly bullish. RSI: {latest['RSI']:.2f}, MACD is positive, and moving averages indicate an uptrend."
        elif confidence > 0.6:
            recommendation = 'Buy'
            reason = f"Technical indicators are moderately bullish. RSI: {latest['RSI']:.2f}, and most signals point to potential upside."
        elif confidence < 0.3:
            recommendation = 'Sell'
            reason = f"Technical indicators are bearish. RSI: {latest['RSI']:.2f}, MACD is negative, and moving averages indicate a downtrend."
        elif confidence < 0.4:
            recommendation = 'Hold/Reduce'
            reason = f"Technical indicators are moderately bearish. RSI: {latest['RSI']:.2f}, and some signals suggest caution."
        else:
            recommendation = 'Neutral'
            reason = f"Technical indicators are mixed. RSI: {latest['RSI']:.2f}, with no clear directional bias."
        
        # Add fundamental context if available
        try:
            pe_ratio = info.get('trailingPE', None)
            market_cap = info.get('marketCap', None)
            
            if pe_ratio and market_cap:
                if market_cap > 1e11:  # Large cap
                    market_size = "large-cap"
                elif market_cap > 1e10:  # Mid cap
                    market_size = "mid-cap"
                else:  # Small cap
                    market_size = "small-cap"
                
                if pe_ratio < 15 and confidence > 0.5:
                    reason += f" Additionally, the stock appears undervalued with a P/E ratio of {pe_ratio:.2f} for a {market_size} company."
                elif pe_ratio > 30 and confidence < 0.5:
                    reason += f" The stock also appears overvalued with a high P/E ratio of {pe_ratio:.2f} for a {market_size} company."
        except:
            pass
        
        return recommendation, confidence, reason
    
    def get_stock_recommendations(self, risk_profile, sector=None, count=3):
        """Get stock recommendations based on risk profile and sector preference"""
        try:
            # Select universe based on risk profile and sector
            if sector and sector.lower() in self.popular_stocks:
                universe = self.popular_stocks[sector.lower()]
            elif risk_profile == "Conservative":
                universe = self.popular_stocks['dividend'] + self.popular_stocks['consumer']
            elif risk_profile == "Moderately Conservative":
                universe = self.popular_stocks['finance'] + self.popular_stocks['consumer']
            elif risk_profile == "Moderate":
                universe = self.popular_stocks['tech'] + self.popular_stocks['healthcare']
            elif risk_profile == "Moderately Aggressive":
                universe = self.popular_stocks['tech'] + self.popular_stocks['growth']
            elif risk_profile == "Aggressive":
                universe = self.popular_stocks['growth']
            else:
                # Default to a mix if risk profile not recognized
                universe = self.popular_stocks['tech'] + self.popular_stocks['finance'] + self.popular_stocks['healthcare']
            
            # Shuffle to get different recommendations each time
            random.shuffle(universe)
            
            # Analyze top stocks
            recommendations = []
            for ticker in universe[:min(10, len(universe))]:  # Analyze up to 10 stocks
                analysis = self.analyze_stock(ticker)
                if analysis['recommendation'] in ['Strong Buy', 'Buy']:
                    recommendations.append({
                        'ticker': ticker,
                        'recommendation': analysis['recommendation'],
                        'confidence': analysis['confidence'],
                        'reason': analysis['reason']
                    })
            
            # Sort by confidence
            recommendations.sort(key=lambda x: x['confidence'], reverse=True)
            
            return recommendations[:count]  # Return top N recommendations
            
        except Exception as e:
            print(f"Error getting recommendations: {str(e)}")
            return []
    
    def process_query(self, query, user_risk_profile="Moderate"):
        """Process a user query and generate a response"""
        query = query.lower()
        
        # Check for stock analysis request
        stock_pattern = r'\b([A-Za-z]{1,5})\b'
        stock_matches = re.findall(stock_pattern, query)
        
        # Filter out common words that might match the pattern
        common_words = ['a', 'i', 'is', 'am', 'are', 'the', 'and', 'or', 'for', 'to', 'in', 'on', 'at', 'by', 'as', 'an', 'be', 'it', 'do', 'if', 'of', 'buy', 'sell']
        potential_tickers = [ticker.upper() for ticker in stock_matches if ticker.lower() not in common_words]
        
        # Check for specific stock analysis
        for ticker in potential_tickers:
            if any(keyword in query for keyword in ["analyze", "analysis", "think of", "opinion on", "should i buy", "recommend"]):
                try:
                    # Validate ticker
                    stock_data = yf.download(ticker, period="1d")
                    if not stock_data.empty:
                        analysis = self.analyze_stock(ticker)
                        return self._format_stock_analysis(ticker, analysis)
                except:
                    continue
        
        # Check for recommendation requests
        if any(keyword in query for keyword in ["recommend", "suggestion", "what should i buy", "what to invest in"]):
            sector = None
            
            # Check for sector-specific recommendations
            sectors = ["tech", "technology", "finance", "financial", "healthcare", "consumer", "industrial", "energy", "dividend", "growth"]
            for s in sectors:
                if s in query:
                    if s == "technology":
                        sector = "tech"
                    elif s == "financial":
                        sector = "finance"
                    else:
                        sector = s
                    break
            
            recommendations = self.get_stock_recommendations(user_risk_profile, sector, count=3)
            return self._format_recommendations(recommendations, user_risk_profile, sector)
        
        # Check for market sentiment
        if any(keyword in query for keyword in ["market", "overall", "sentiment", "trend", "outlook"]):
            return self._format_market_sentiment()
        
        # Check for educational questions
        if any(keyword in query for keyword in ["what is", "how does", "explain", "definition", "mean"]):
            return self._provide_educational_content(query)
        
        # Default response
        return "I'm here to help with stock analysis and investment recommendations. You can ask me to analyze a specific stock (e.g., 'What do you think of AAPL?'), get recommendations based on your risk profile, or ask about market sentiment."
    
    def _format_stock_analysis(self, ticker, analysis):
        """Format stock analysis as a readable response"""
        try:
            # Get additional stock info
            stock = yf.Ticker(ticker)
            info = stock.info
            company_name = info.get('shortName', ticker)
            sector = info.get('sector', 'Unknown sector')
            industry = info.get('industry', 'Unknown industry')
            
            # Get current price
            current_data = yf.download(ticker, period="1d")
            current_price = current_data['Close'].iloc[-1] if not current_data.empty else "Unknown"
            
            # Format response
            response = f"## Analysis of {company_name} ({ticker})\n\n"
            response += f"*Sector:* {sector} | *Industry:* {industry}\n\n"
            response += f"*Current Price:* ${current_price:.2f}\n\n"
            response += f"*Recommendation:* {analysis['recommendation']}\n"
            response += f"*Confidence:* {analysis['confidence']*100:.1f}%\n\n"
            response += f"*Analysis:* {analysis['reason']}\n\n"
            
            # Add some fundamental data if available
            pe_ratio = info.get('trailingPE', None)
            market_cap = info.get('marketCap', None)
            dividend_yield = info.get('dividendYield', None)
            
            response += "*Key Metrics:*\n"
            
            if market_cap:
                if market_cap >= 1e12:
                    market_cap_str = f"${market_cap/1e12:.2f}T"
                elif market_cap >= 1e9:
                    market_cap_str = f"${market_cap/1e9:.2f}B"
                else:
                    market_cap_str = f"${market_cap/1e6:.2f}M"
                response += f"- Market Cap: {market_cap_str}\n"
            
            if pe_ratio:
                response += f"- P/E Ratio: {pe_ratio:.2f}\n"
            
            if dividend_yield:
                response += f"- Dividend Yield: {dividend_yield*100:.2f}%\n"
            
            response += "\n*Disclaimer:* This analysis is based on technical indicators and historical data. Always conduct your own research before making investment decisions."
            
            return response
            
        except Exception as e:
            print(f"Error formatting analysis for {ticker}: {str(e)}")
            return f"Here's my analysis of {ticker}:\n\n*Recommendation:* {analysis['recommendation']}\n*Confidence:* {analysis['confidence']*100:.1f}%\n\n{analysis['reason']}"
    
    def _format_recommendations(self, recommendations, risk_profile, sector=None):
        """Format stock recommendations as a readable response"""
        if not recommendations:
            if sector:
                return f"Based on your {risk_profile} risk profile, I don't have strong {sector} sector recommendations at the moment. The market conditions may be uncertain for your risk level. Consider consulting with a financial advisor for personalized advice."
            else:
                return f"Based on your {risk_profile} risk profile, I don't have strong recommendations at the moment. The market conditions may be uncertain for your risk level. Consider consulting with a financial advisor for personalized advice."
        
        sector_text = f" in the {sector} sector" if sector else ""
        response = f"## Stock Recommendations for {risk_profile} Investor{sector_text}\n\n"
        response += f"Based on your {risk_profile} risk profile and current market conditions, here are my top recommendations:\n\n"
        
        for i, rec in enumerate(recommendations):
            response += f"### {i+1}. {rec['ticker']}\n"
            response += f"*Recommendation:* {rec['recommendation']} (Confidence: {rec['confidence']*100:.1f}%)\n"
            response += f"{rec['reason']}\n\n"
        
        response += "*Note:* These recommendations are based on technical analysis and may not account for all factors. Always conduct your own research before making investment decisions."
        
        return response
    
    def _format_market_sentiment(self):
        """Format market sentiment as a readable response"""
        # Refresh market sentiment
        self.market_sentiment = self._get_market_sentiment()
        
        response = "## Current Market Sentiment\n\n"
        
        if self.market_sentiment == "bullish":
            response += "The overall market sentiment appears *bullish* at the moment. Major indices have shown positive momentum over the past week.\n\n"
            response += "In bullish markets, growth stocks and cyclical sectors often perform well. Consider looking at technology, consumer discretionary, and industrial sectors for opportunities.\n\n"
        elif self.market_sentiment == "bearish":
            response += "The overall market sentiment appears *bearish* at the moment. Major indices have shown negative momentum over the past week.\n\n"
            response += "In bearish markets, defensive sectors often outperform. Consider looking at utilities, consumer staples, and healthcare for more stability. Dividend-paying stocks may also provide income during market downturns.\n\n"
        else:
            response += "The overall market sentiment appears *neutral* at the moment. Major indices have been relatively stable over the past week.\n\n"
            response += "In neutral markets, it's important to focus on individual stock selection rather than broad sector trends. Look for companies with strong fundamentals and reasonable valuations.\n\n"
        
        response += "*Remember:* Market sentiment can change quickly. It's important to maintain a diversified portfolio aligned with your long-term investment goals and risk tolerance."
        
        return response
    
    def _provide_educational_content(self, query):
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
            
            "rsi": "The Relative Strength Index (RSI) is a momentum oscillator that measures the speed and change of price movements. The RSI ranges from 0 to 100 and is typically used to identify overbought or oversold conditions in a market. Traditionally, an RSI reading of 70 or above indicates an overbought condition, while a reading of 30 or below indicates an oversold condition.",
            
            "macd": "The Moving Average Convergence Divergence (MACD) is a trend-following momentum indicator that shows the relationship between two moving averages of a security's price. The MACD is calculated by subtracting the 26-period Exponential Moving Average (EMA) from the 12-period EMA. A nine-day EMA of the MACD, called the 'signal line', is then plotted on top of the MACD, functioning as a trigger for buy and sell signals.",
            
            "bollinger bands": "Bollinger Bands are a type of statistical chart characterizing the prices and volatility over time of a financial instrument or commodity. They consist of a middle band (usually a simple moving average) and two outer bands that are standard deviations away from the middle band. Bollinger Bands help identify whether prices are high or low on a relative basis, and can be used to identify potential trend reversals."
        }
        
        # Check for educational keywords in the query
        for term, explanation in investment_education.items():
            if term in query.lower():
                return f"{term.upper()}: {explanation}"
        
        # If no specific term is found, provide a general response
        return "I can provide information about various investment concepts like stocks, bonds, ETFs, mutual funds, dividends, P/E ratios, market capitalization, bull markets, bear markets, volatility, diversification, asset allocation, RSI, MACD, and Bollinger Bands. Please ask about a specific term you'd like to learn more about."