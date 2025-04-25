import os
import requests
from datetime import datetime, timedelta

def get_company_logo(ticker):
    """Get company logo from clearbit API"""
    try:
        # Try to get logo from clearbit
        url = f"https://logo.clearbit.com/{ticker.lower().replace('.', '')}.com"
        response = requests.get(url)
        if response.status_code == 200:
            return url
        else:
            # Fallback to a default icon
            return "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Flat_stock_icon.svg/1024px-Flat_stock_icon.svg.png"
    except:
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Flat_stock_icon.svg/1024px-Flat_stock_icon.svg.png"

def get_stock_news(ticker, limit=5):
    """Get news for a specific stock using NewsAPI"""
    try:
        # You should store this in environment variables or config
        NEWS_API_KEY = "decadae799b744b1833f0cb49a31c3a4"  
        
        # Convert ticker symbol to company name for better search results
        # Remove common stock symbols
        search_term = ticker.replace('^', '').replace('.', ' ')
        
        # Calculate date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Construct the API URL
        base_url = "https://newsapi.org/v2/everything"
        
        params = {
            'q': search_term,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': limit,
            'apiKey': NEWS_API_KEY
        }
        
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            news_data = response.json()
            
            if news_data['status'] == 'ok' and news_data['totalResults'] > 0:
                formatted_news = []
                
                for article in news_data['articles'][:limit]:
                    # Convert timestamp to datetime
                    pub_date = datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                    formatted_date = pub_date.strftime('%Y-%m-%d %H:%M')
                    
                    news_item = {
                        'title': article['title'],
                        'publisher': article['source']['name'],
                        'link': article['url'],
                        'published': formatted_date,
                        'summary': article['description']
                    }
                    formatted_news.append(news_item)
                
                return formatted_news
            
        return []  # Return empty list if no news found
        
    except Exception as e:
        print(f"Error fetching news for {ticker}: {str(e)}")
        return []
