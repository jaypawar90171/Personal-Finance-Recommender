import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# Function to fetch stock data
def fetch_stock_data(ticker, start_date, end_date):
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    return stock_data


# Function to calculate moving average
def calculate_moving_average(data, window):
    return data['Close'].rolling(window=window).mean()


# Function to plot stock data
def plot_stock_data(data, ticker, moving_avg_50, moving_avg_200):
    plt.figure(figsize=(14, 7))
    plt.plot(data['Close'], label=f'{ticker} Close Price', color='blue')
    plt.plot(moving_avg_50, label='50-Day Moving Average', color='orange')
    plt.plot(moving_avg_200, label='200-Day Moving Average', color='green')
    plt.title(f'{ticker} Stock Price and Moving Averages')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.legend()
    plt.show()


# Function to perform basic analysis
def analyze_stock(data):
    # Calculate daily returns
    data['Daily Return'] = data['Close'].pct_change()

    # Calculate cumulative returns
    data['Cumulative Return'] = (1 + data['Daily Return']).cumprod()

    # Print summary statistics
    print("Summary Statistics:")
    print(data['Daily Return'].describe())

    # Plot daily returns
    plt.figure(figsize=(14, 7))
    plt.plot(data['Daily Return'], label='Daily Return', color='purple')
    plt.title('Daily Returns')
    plt.xlabel('Date')
    plt.ylabel('Daily Return')
    plt.legend()
    plt.show()

    # Plot cumulative returns
    plt.figure(figsize=(14, 7))
    plt.plot(data['Cumulative Return'], label='Cumulative Return', color='red')
    plt.title('Cumulative Returns')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Return')
    plt.legend()
    plt.show()


# Main function to analyze multiple stocks
def analyze_multiple_stocks(tickers, start_date, end_date):
    for ticker in tickers:
        print(f"Analyzing {ticker}...")
        stock_data = fetch_stock_data(ticker, start_date, end_date)

        # Calculate moving averages
        stock_data['50_MA'] = calculate_moving_average(stock_data, 50)
        stock_data['200_MA'] = calculate_moving_average(stock_data, 200)

        # Plot stock data with moving averages
        plot_stock_data(stock_data, ticker, stock_data['50_MA'], stock_data['200_MA'])

        # Perform basic analysis
        analyze_stock(stock_data)


# List of stock tickers to analyze
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']

# Date range for analysis
start_date = '2020-01-01'
end_date = '2023-01-01'

# Analyze multiple stocks
analyze_multiple_stocks(tickers, start_date, end_date)