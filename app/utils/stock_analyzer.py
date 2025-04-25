import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

class StockAnalyzer:
    def __init__(self):
        self.risk_tolerance = None
    
    def fetch_stock_data(self, ticker, start_date, end_date):
        """Fetch historical stock data"""
        try:
            data = yf.download(ticker, start=start_date, end=end_date)
            if data.empty:
                return None
            return data
        except:
            return None
    
    def process_stock_data(self, data):
        """Process stock data and handle DatetimeIndex"""
        if data is None or data.empty:
            return None
            
        # Convert DatetimeIndex to regular datetime column if needed
        if isinstance(data.index, pd.DatetimeIndex):
            data = data.reset_index()
            data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')
        
        return data

    def calculate_technical_indicators(self, data):
        """Calculate technical indicators for the stock data"""
        if data is None or data.empty:
            return None
        
        # Process data to handle DatetimeIndex
        data = self.process_stock_data(data)
        
        # Set Date as index again for calculations
        if 'Date' in data.columns:
            data = data.set_index('Date')
        
        # Calculate daily returns
        if isinstance(data['Close'], pd.DataFrame) or len(data['Close'].shape) > 1:
            data['Close'] = data['Close'].squeeze()  # Convert to 1D Series if it's a DataFrame or 2D array

        data['Daily_Return'] = data['Close'].pct_change()
        
        # Calculate moving averages
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['MA50'] = data['Close'].rolling(window=50).mean()
        data['MA200'] = data['Close'].rolling(window=200).mean()
        
        # Calculate Bollinger Bands
        data['STD20'] = data['Close'].rolling(window=20).std()
        data['Upper_Band'] = data['MA20'] + (data['STD20'] * 2)
        data['Lower_Band'] = data['MA20'] - (data['STD20'] * 2)
        
        # Calculate RSI
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Calculate MACD
        data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
        data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = data['EMA12'] - data['EMA26']
        data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
        data['MACD_Histogram'] = data['MACD'] - data['Signal_Line']
        
        # Calculate volume moving average
        data['Volume_MA50'] = data['Volume'].rolling(window=50).mean()
        
        return data
    
    def calculate_risk_metrics(self, data, benchmark_data=None):
        """Calculate risk metrics for the stock"""
        if data is None or data.empty:
            return {}
        
        # Calculate volatility
        daily_returns = data['Daily_Return'].dropna()
        daily_volatility = daily_returns.std()
        annual_volatility = daily_volatility * np.sqrt(252)  # Assuming 252 trading days in a year
        
        # Calculate Sharpe Ratio (assuming risk-free rate of 0.02 or 2%)
        risk_free_rate = 0.02
        excess_return = daily_returns.mean() * 252 - risk_free_rate
        sharpe_ratio = excess_return / annual_volatility if annual_volatility > 0 else 0
        
        # Calculate Sortino Ratio (downside risk only)
        negative_returns = daily_returns[daily_returns < 0]
        downside_deviation = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0.0001
        sortino_ratio = excess_return / downside_deviation if downside_deviation > 0 else 0
        
        # Calculate maximum drawdown
        cumulative_returns = (1 + daily_returns).cumprod()
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns / running_max) - 1
        max_drawdown = drawdown.min()
        
        # Calculate Beta and Alpha if benchmark data is provided
        beta = np.nan
        alpha = np.nan
        
        if benchmark_data is not None and not benchmark_data.empty:
            # Calculate benchmark returns
            benchmark_data['Daily_Return'] = benchmark_data['Close'].pct_change()
            benchmark_returns = benchmark_data['Daily_Return'].dropna()
            
            # Align the data
            common_dates = daily_returns.index.intersection(benchmark_returns.index)
            if len(common_dates) > 0:
                aligned_returns = daily_returns.loc[common_dates]
                aligned_benchmark = benchmark_returns.loc[common_dates]
                
                # Calculate Beta
                covariance = aligned_returns.cov(aligned_benchmark)
                benchmark_variance = aligned_benchmark.var()
                beta = covariance / benchmark_variance if benchmark_variance > 0 else np.nan
                
                # Calculate Alpha (Jensen's Alpha)
                stock_return = aligned_returns.mean() * 252
                market_return = aligned_benchmark.mean() * 252
                alpha = stock_return - (risk_free_rate + beta * (market_return - risk_free_rate))
        
        return {
            'Volatility (Daily)': daily_volatility,
            'Volatility (Annual)': annual_volatility,
            'Sharpe Ratio (Annual)': sharpe_ratio,
            'Sortino Ratio (Annual)': sortino_ratio,
            'Max Drawdown': max_drawdown,
            'Beta': beta,
            'Alpha': alpha
        }
    
    def fetch_fundamental_data(self, ticker):
        """Fetch fundamental data for a stock"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extract relevant fundamental data
            fundamentals = {
                'shortName': info.get('shortName', ticker),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'Business Summary': info.get('longBusinessSummary', 'No business summary available.'),
                'Market Cap': self._format_market_cap(info.get('marketCap', 0)),
                'P/E Ratio': self._format_value(info.get('trailingPE', None)),
                'Forward P/E': self._format_value(info.get('forwardPE', None)),
                'PEG Ratio': self._format_value(info.get('pegRatio', None)),
                'EPS': self._format_value(info.get('trailingEps', None)),
                'Dividend Yield (%)': self._format_percentage(info.get('dividendYield', None)),
                'Profit Margin': self._format_percentage(info.get('profitMargins', None)),
                'ROE': self._format_percentage(info.get('returnOnEquity', None)),
                'Debt to Equity': self._format_value(info.get('debtToEquity', None))
            }
            
            return fundamentals
        except:
            return {}
    
    def _format_market_cap(self, value):
        """Format market cap value"""
        if value is None or value == 0:
            return 'N/A'
        
        if value >= 1e12:
            return f"${value/1e12:.2f}T"
        elif value >= 1e9:
            return f"${value/1e9:.2f}B"
        elif value >= 1e6:
            return f"${value/1e6:.2f}M"
        else:
            return f"${value:.2f}"
    
    def _format_value(self, value):
        """Format numeric value"""
        if value is None or np.isnan(value):
            return 'N/A'
        return f"{value:.2f}"
    
    def _format_percentage(self, value):
        """Format percentage value"""
        if value is None or np.isnan(value):
            return 'N/A'
        return f"{value*100:.2f}%"
    
    def evaluate_stock_suitability(self, ticker, risk_metrics, risk_tolerance):
        """Evaluate if a stock is suitable for the user's risk tolerance"""
        if not risk_metrics or not risk_tolerance:
            return None
        
        # Extract risk metrics
        volatility = risk_metrics.get('Volatility (Annual)', 0) * 100  # Convert to percentage
        beta = risk_metrics.get('Beta', 1.0)
        sharpe = risk_metrics.get('Sharpe Ratio (Annual)', 0)
        max_drawdown = abs(risk_metrics.get('Max Drawdown', 0)) * 100  # Convert to percentage
        
        # Get user's risk tolerance score
        risk_score = risk_tolerance.get('score', 50)
        
        # Evaluate each risk factor
        volatility_rating = self._evaluate_volatility(volatility, risk_score)
        beta_rating = self._evaluate_beta(beta, risk_score)
        sharpe_rating = self._evaluate_sharpe(sharpe)
        drawdown_rating = self._evaluate_drawdown(max_drawdown, risk_score)
        
        # Calculate overall suitability score (0-100)
        overall_score = (
            volatility_rating['Score'] * 0.3 +
            beta_rating['Score'] * 0.3 +
            sharpe_rating['Score'] * 0.2 +
            drawdown_rating['Score'] * 0.2
        )
        
        # Determine match rating
        match_rating = "Excellent Match"
        match_description = f"{ticker} aligns very well with your risk tolerance."
        
        if overall_score < 70:
            match_rating = "Good Match"
            match_description = f"{ticker} generally aligns with your risk tolerance with some considerations."
        
        if overall_score < 50:
            match_rating = "Moderate Match"
            match_description = f"{ticker} may be more volatile than your risk tolerance suggests. Consider as a smaller position."
        
        if overall_score < 30:
            match_rating = "Poor Match"
            match_description = f"{ticker} appears too risky for your risk profile. Consider alternatives or a very small position."
        
        return {
            'Overall Suitability Score': overall_score,
            'Match Rating': match_rating,
            'Match Description': match_description,
            'Volatility': volatility_rating,
            'Beta': beta_rating,
            'Sharpe Ratio': sharpe_rating,
            'Max Drawdown': drawdown_rating
        }
    
    def _evaluate_volatility(self, volatility, risk_score):
        """Evaluate volatility against risk tolerance"""
        # Conservative: <15%, Moderate: 15-25%, Aggressive: >25%
        if risk_score < 30:  # Conservative
            if volatility < 15:
                return {'Rating': 'Good', 'Score': 90}
            elif volatility < 20:
                return {'Rating': 'Moderate', 'Score': 60}
            else:
                return {'Rating': 'High', 'Score': 30}
        elif risk_score < 70:  # Moderate
            if volatility < 15:
                return {'Rating': 'Low', 'Score': 70}
            elif volatility < 25:
                return {'Rating': 'Good', 'Score': 90}
            else:
                return {'Rating': 'High', 'Score': 50}
        else:  # Aggressive
            if volatility < 15:
                return {'Rating': 'Low', 'Score': 50}
            elif volatility < 25:
                return {'Rating': 'Moderate', 'Score': 70}
            else:
                return {'Rating': 'Good', 'Score': 90}
    
    def _evaluate_beta(self, beta, risk_score):
        """Evaluate beta against risk tolerance"""
        if np.isnan(beta):
            return {'Rating': 'Neutral', 'Score': 50}
        
        # Conservative: <0.8, Moderate: 0.8-1.2, Aggressive: >1.2
        if risk_score < 30:  # Conservative
            if beta < 0.8:
                return {'Rating': 'Good', 'Score': 90}
            elif beta < 1.0:
                return {'Rating': 'Moderate', 'Score': 60}
            else:
                return {'Rating': 'High', 'Score': 30}
        elif risk_score < 70:  # Moderate
            if beta < 0.8:
                return {'Rating': 'Low', 'Score': 70}
            elif beta < 1.2:
                return {'Rating': 'Good', 'Score': 90}
            else:
                return {'Rating': 'High', 'Score': 50}
        else:  # Aggressive
            if beta < 0.8:
                return {'Rating': 'Low', 'Score': 50}
            elif beta < 1.2:
                return {'Rating': 'Moderate', 'Score': 70}
            else:
                return {'Rating': 'Good', 'Score': 90}
    
    def _evaluate_sharpe(self, sharpe):
        """Evaluate Sharpe ratio"""
        if sharpe < 0:
            return {'Rating': 'Poor', 'Score': 20}
        elif sharpe < 0.5:
            return {'Rating': 'Below Average', 'Score': 40}
        elif sharpe < 1.0:
            return {'Rating': 'Average', 'Score': 60}
        elif sharpe < 1.5:
            return {'Rating': 'Good', 'Score': 80}
        else:
            return {'Rating': 'Excellent', 'Score': 100}
    
    def _evaluate_drawdown(self, max_drawdown, risk_score):
        """Evaluate maximum drawdown against risk tolerance"""
        # Conservative: <15%, Moderate: 15-30%, Aggressive: >30%
        if risk_score < 30:  # Conservative
            if max_drawdown < 15:
                return {'Rating': 'Good', 'Score': 90}
            elif max_drawdown < 25:
                return {'Rating': 'Moderate', 'Score': 60}
            else:
                return {'Rating': 'High', 'Score': 30}
        elif risk_score < 70:  # Moderate
            if max_drawdown < 15:
                return {'Rating': 'Low', 'Score': 70}
            elif max_drawdown < 30:
                return {'Rating': 'Good', 'Score': 90}
            else:
                return {'Rating': 'High', 'Score': 50}
        else:  # Aggressive
            if max_drawdown < 20:
                return {'Rating': 'Low', 'Score': 50}
            elif max_drawdown < 35:
                return {'Rating': 'Moderate', 'Score': 70}
            else:
                return {'Rating': 'Good', 'Score': 90}

def safe_series_convert(value, default=0.0):
    """Safely convert pandas Series or other types to float"""
    try:
        if isinstance(value, pd.Series):
            if len(value) > 0:
                # Handle datetime values
                if pd.api.types.is_datetime64_any_dtype(value):
                    return value.iloc[0].strftime('%Y-%m-%d')
                return float(value.iloc[0])
            return default
        elif isinstance(value, pd.DatetimeIndex):
            if len(value) > 0:
                return value[0].strftime('%Y-%m-%d')
            return default
        return float(value)
    except (TypeError, ValueError):
        # Return the original value if it's a string or non-numeric type
        if isinstance(value, str):
            return value
        return default