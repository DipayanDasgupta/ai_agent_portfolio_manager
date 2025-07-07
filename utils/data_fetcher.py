import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import time
import streamlit as st
import yfinance as yf
import finnhub
import google.generativeai as genai
from .database_manager import DatabaseManager
import logging

class DataFetcher:
    def __init__(self):
        # Get API keys from environment variables
        self.finnhub_key = os.getenv('FINNHUB_API_KEY', "d1fh2ehr01qig3h1pohgd1fh2ehr01qig3h1poi0")
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        
        self.cache_duration = 300  # 5 minutes cache
        self.db = DatabaseManager()
         
        # Initialize Finnhub client
        try:
            self.finnhub_client = finnhub.Client(api_key=self.finnhub_key)
        except Exception as e:
            st.error(f"Error initializing Finnhub client: {str(e)}")
            self.finnhub_client = None

        # Initialize Gemini client
        try:
            if self.gemini_key:
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.5-pro')
            else:
                st.error("GEMINI_API_KEY not found. Please add it to your environment variables.")
                self.gemini_model = None
        except Exception as e:
            st.error(f"Error initializing Gemini client: {str(e)}")
            self.gemini_model = None

        # Setup logging
        self.logger = logging.getLogger('data_fetcher')
        self.logger.info("Initialized DataFetcher for Indian stocks with yfinance, Finnhub, and Gemini")

        # Define representative stocks for news fetching (consistent with AIAnalyzer and RiskCalculator)
        self.nifty_tickers = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS', 'HINDUNILVR.NS', 'DABUR.NS', 'UPL.NS']

    def get_stock_data(self, symbol, period='1day'):
        """Fetch stock data for Indian stocks using yfinance as primary source, Finnhub as backup"""
        try:
            # Check database cache (1 hour freshness)
            if self.db.data_freshness_check(symbol, 'stock', max_age_hours=1):
                cached_data = self.db.get_market_data(symbol, 'stock', days_back=30)
                if cached_data is not None and not cached_data.empty:
                    self.logger.info(f"Using cached data for {symbol}")
                    df = cached_data.set_index('timestamp')[
                        ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
                    ]
                    df.columns = ['open', 'high', 'low', 'close', 'volume']
                    for col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').astype(float)
                    return df

            # Try yfinance first
            self.logger.info(f"Trying yfinance for {symbol}")
            df = self._get_stock_data_yfinance(symbol)
            if not df.empty:
                return df

            # Fall back to Finnhub if yfinance fails
            if self.finnhub_client:
                self.logger.info(f"yfinance failed, trying Finnhub for {symbol}")
                return self._get_stock_data_finnhub(symbol)

            self.logger.warning(f"No data available for {symbol} from yfinance or Finnhub")
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error in get_stock_data for {symbol}: {str(e)}")
            return pd.DataFrame()

    # In utils/data_fetcher.py, inside the DataFetcher class

    def get_stock_data(self, symbol, period='1mo'): # Changed default period to get more data
        """Fetch stock data for Indian stocks using yfinance as primary source, with database caching."""
        try:
            # 1. Check database cache for fresh data (1 hour freshness)
            if self.db.data_freshness_check(symbol, 'stock', max_age_hours=1):
                cached_data = self.db.get_market_data(symbol, 'stock', days_back=365)
                if cached_data is not None and not cached_data.empty:
                    self.logger.info(f"Using CACHED data for {symbol}")
                    # Prepare dataframe for use
                    df = cached_data.set_index(pd.to_datetime(cached_data['timestamp']))
                    df = df[['open_price', 'high_price', 'low_price', 'close_price', 'volume']]
                    df.columns = ['open', 'high', 'low', 'close', 'volume']
                    return df.astype(float)

            # 2. If no fresh cache, fetch from yfinance
            self.logger.info(f"Cache miss or stale. Fetching LIVE data for {symbol} from yfinance.")
            stock = yf.Ticker(symbol)
            # Fetch 1 year of data to ensure enough for calculations
            df = stock.history(period="1y", interval="1d", auto_adjust=False) 
            
            if df.empty:
                self.logger.warning(f"No yfinance data found for {symbol}.")
                return pd.DataFrame()

            # 3. Store the newly fetched data in the database
            df_for_db = df.copy()
            # Ensure column names are consistent for the database
            df_for_db.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
            df_for_db['timestamp'] = df_for_db.index
            self.db.store_market_data(symbol, 'stock', df_for_db)
            
            self.logger.info(f"Successfully fetched and stored {symbol} from yfinance")
            return df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})

        except Exception as e:
            self.logger.error(f"Error in get_stock_data for {symbol}: {e}")
            return pd.DataFrame() # Return empty dataframe on error

        except Exception as e:
            self.logger.error(f"yfinance API error for {symbol}: {str(e)}")
            return pd.DataFrame()

    def _get_stock_data_finnhub(self, symbol):
        """Fetch stock data from Finnhub API using free endpoints"""
        try:
            if not self.finnhub_client:
                self.logger.error("Finnhub client not initialized")
                return pd.DataFrame()

            # Use Finnhub quote endpoint for current price
            quote = self.finnhub_client.quote(symbol)
            if not quote or 'c' not in quote or quote['c'] == 0:
                self.logger.warning(f"Finnhub quote invalid for {symbol}: {quote}")
                return pd.DataFrame()

            current_price = quote['c']  # Current price in INR
            high_price = quote['h']  # High price of the day
            low_price = quote['l']  # Low price of the day
            open_price = quote['o']  # Open price of the day
            prev_close = quote['pc']  # Previous close price

            # Fetch historical data (use Finnhub candles endpoint for 30 days)
            end_date = int(datetime.now().timestamp())
            start_date = int((datetime.now() - timedelta(days=30)).timestamp())
            candles = self.finnhub_client.stock_candles(symbol, 'D', start_date, end_date)

            if candles['s'] != 'ok' or not candles.get('c'):
                self.logger.warning(f"No historical data from Finnhub for {symbol}")
                return pd.DataFrame()

            # Create DataFrame from candles
            df_data = {
                'open': candles['o'],
                'high': candles['h'],
                'low': candles['l'],
                'close': candles['c'],
                'volume': candles['v']
            }
            dates = pd.to_datetime(candles['t'], unit='s')
            df = pd.DataFrame(df_data, index=dates)
            df = df.sort_index()

            # Store in database
            df_for_db = df.copy()
            df_for_db['timestamp'] = df_for_db.index
            self.db.store_market_data(symbol, 'stock', df_for_db)
            self.logger.info(f"Successfully fetched {symbol} from Finnhub (current price: ₹{current_price:,.2f})")
            return df

        except Exception as e:
            self.logger.error(f"Finnhub API error for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_economic_indicators(self):
        """Fetch macroeconomic indicators for India using Finnhub"""
        indicators = {}
        try:
            if not self.finnhub_client:
                self.logger.error("Finnhub client not initialized")
                return indicators

            # Fetch India-specific economic indicators via Finnhub economic calendar
            try:
                economic_data = self.finnhub_client.economic_calendar()
                if economic_data and 'economicCalendar' in economic_data:
                    for event in economic_data['economicCalendar']:
                        if 'India' in event.get('country', '') and 'actual' in event:
                            date = event.get('eventTime', datetime.now().strftime('%Y-%m-%d'))
                            if 'CPI' in event['event']:
                                indicators['india_cpi'] = {'value': float(event['actual']), 'date': date}
                            elif 'GDP' in event['event']:
                                indicators['india_gdp_growth'] = {'value': float(event['actual']), 'date': date}
                            elif 'Interest Rate' in event['event'] or 'Repo Rate' in event['event']:
                                indicators['rbi_repo_rate'] = {'value': float(event['actual']), 'date': date}
            except Exception as e:
                self.logger.warning(f"Could not fetch economic indicators from Finnhub: {str(e)}")

            if not indicators:
                self.logger.warning("No economic indicators available from Finnhub for India")
            else:
                self.logger.info("Fetched economic indicators for India from Finnhub")
            return indicators

        except Exception as e:
            st.warning(f"Could not fetch economic indicators: {str(e)}")
            return indicators

    @st.cache_data(ttl=1800)
    def get_market_news(self):
        """Fetch and analyze market news for Indian stocks using Gemini"""
        if not self.gemini_model:
            self.logger.error("Gemini model not initialized")
            return []

        try:
            # Fetch recent news from Finnhub for representative Nifty stocks
            news_items = []
            if self.finnhub_client:
                for symbol in self.nifty_tickers[:5]:  # Limit to avoid rate limits
                    try:
                        news = self.finnhub_client.company_news(
                            symbol,
                            _from=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                            to=datetime.now().strftime('%Y-%m-%d')
                        )
                        for item in news[:2]:  # Take top 2 news per symbol
                            news_items.append({
                                'title': item.get('headline', 'No title'),
                                'summary': item.get('summary', 'No summary'),
                                'url': item.get('url', ''),
                                'time_published': datetime.fromtimestamp(item.get('datetime', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                                'source': item.get('source', 'Unknown')
                            })
                    except Exception as e:
                        self.logger.warning(f"Could not fetch news for {symbol} from Finnhub: {str(e)}")

            if not news_items:
                self.logger.warning("No news data available from Finnhub")
                return []

            # Analyze news sentiment with Gemini
            news_summary = ""
            for item in news_items[:5]:  # Limit to top 5 news items
                news_summary += f"- {item['title']}: {item['summary'][:100]}...\n"

            prompt = f"""
            Analyze the sentiment and implications of these recent market news items for the Indian market:
            
            {news_summary}
            
            Please provide:
            1. Overall market sentiment (Bullish/Bearish/Neutral)
            2. Key themes or trends identified (e.g., policy changes, sector performance)
            3. Potential impact on Indian stock sectors (e.g., IT, Banking, FMCG, Auto, Pharma)
            4. One actionable insight for portfolio positioning in India
            
            Keep the analysis concise and focused on investment implications for Indian investors.
            """
            try:
                response = self.gemini_model.generate_content(
                    contents=prompt,
                    generation_config={
                        'max_output_tokens': 5000,
                        'temperature': 0.3
                    },
                    request_options={'timeout': 120}
                )
                analysis = response.text
            except Exception as e:
                self.logger.error(f"Gemini news sentiment analysis failed: {str(e)}")
                return news_items  # Return raw news without sentiment

            # Append Gemini analysis to news items
            for item in news_items:
                item['overall_sentiment_score'] = 0  # Placeholder, as Gemini provides textual sentiment
                item['overall_sentiment_label'] = analysis.split('\n')[0].replace('1. Overall market sentiment: ', '') if analysis else 'Neutral'
                item['analysis'] = analysis

            self.logger.info("Successfully fetched and analyzed market news with Gemini")
            return news_items

        except Exception as e:
            st.warning(f"Could not fetch or analyze market news: {str(e)}")
            return []

    def get_sector_performance(self):
        """Get sector performance data for Indian market using yfinance"""
        try:
            # Define major Indian sectors (consistent with RiskCalculator and AIAnalyzer)
            sector_map = {
                'Nifty IT': 'NIFTYIT.NS',
                'Nifty Bank': 'BANKNIFTY.NS',
                'Nifty FMCG': 'NIFTYFMCG.NS',
                'Nifty Auto': 'NIFTYAUTO.NS',
                'Nifty Pharma': 'NIFTYPHARMA.NS'
            }
            performance = {}
            for sector, ticker in sector_map.items():
                try:
                    df = self.get_stock_data(ticker)
                    if not df.empty:
                        returns = df['close'].pct_change(periods=30).iloc[-1] * 100  # 30-day return
                        performance[sector] = round(returns, 2)
                except Exception as e:
                    self.logger.warning(f"Could not fetch data for {sector} ({ticker}): {str(e)}")
            self.logger.info("Fetched sector performance for Indian market")
            return performance

        except Exception as e:
            st.warning(f"Could not fetch sector performance: {str(e)}")
            return {}

    def calculate_correlation_matrix(self, symbols, period_days=252):
        """Calculate correlation matrix for given Indian stock symbols"""
        try:
            price_data = {}
            for symbol in symbols:
                data = self.get_stock_data(symbol)
                if data is not None and not data.empty:
                    recent_data = data.tail(period_days)
                    price_data[symbol] = recent_data['close']

            if len(price_data) < 2:
                self.logger.warning("Insufficient data for correlation matrix")
                return pd.DataFrame()

            # Create DataFrame and calculate correlation
            df = pd.DataFrame(price_data)
            df = df.dropna()
            if df.empty:
                self.logger.warning("No overlapping data for correlation matrix")
                return pd.DataFrame()

            correlation_matrix = df.corr()
            self.logger.info("Successfully calculated correlation matrix")
            return correlation_matrix

        except Exception as e:
            st.error(f"Error calculating correlation matrix: {str(e)}")
            return pd.DataFrame()

    def get_volatility_data(self, symbols, period_days=30):
        """Calculate volatility for given Indian stock symbols"""
        volatility_data = {}
        for symbol in symbols:
            try:
                data = self.get_stock_data(symbol)
                if data is not None and not data.empty:
                    recent_data = data.tail(period_days + 1)
                    returns = recent_data['close'].pct_change().dropna()
                    volatility = returns.std() * np.sqrt(252)  # Annualized
                    volatility_data[symbol] = volatility
            except Exception as e:
                self.logger.warning(f"Could not calculate volatility for {symbol}: {str(e)}")
        self.logger.info("Successfully calculated volatility data")
        return volatility_data