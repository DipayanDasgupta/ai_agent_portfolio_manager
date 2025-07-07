import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

class DatabaseManager:
    def __init__(self):
        """Initialize database connection - SQLite by default, PostgreSQL if available"""
        self.logger = logging.getLogger(__name__)
        self.conn = None
        self.db_available = False
        self.db_type = "none"
        
        # Try PostgreSQL first (for production/advanced users)
        database_url = os.getenv('DATABASE_URL')
        if database_url and database_url.startswith('postgresql'):
            try:
                self.conn = psycopg2.connect(database_url)
                self.conn.autocommit = True
                self.db_available = True
                self.db_type = "postgresql"
                self.logger.info("Connected to PostgreSQL database")
                self.init_tables_postgresql()
                return
            except Exception as e:
                self.logger.warning(f"PostgreSQL connection failed: {str(e)}, falling back to SQLite")
        
        # Use SQLite as default (lightweight, no setup required)
        try:
            os.makedirs('data', exist_ok=True)
            db_path = os.path.join('data', 'portfolio_manager.db')
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            self.db_available = True
            self.db_type = "sqlite"
            self.logger.info(f"Connected to SQLite database at {db_path}")
            self.init_tables_sqlite()
        except Exception as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
            self.conn = None
            self.db_available = False
    
   # In utils/database_manager.py

    def init_tables_sqlite(self):
        """Initialize SQLite database tables for Indian market"""
        try:
            cursor = self.conn.cursor()
            
            # Market data table for Indian stocks and indices
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    asset_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    close_price REAL,
                    volume INTEGER,
                    market_cap REAL,
                    additional_data TEXT, -- FIX: Added this column
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, asset_type, timestamp)
                )
            """)
            
            # FIX: Add 'country' and 'change' columns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS economic_indicators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    indicator_name TEXT NOT NULL,
                    value TEXT,
                    change TEXT, -- FIX: Added this column
                    country TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(indicator_name, country)
                )
            """)

            # FIX: Add the missing market_news table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    summary TEXT,
                    source TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # FIX: Add the missing market_analysis table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    analysis TEXT,
                    source TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Portfolio recommendations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_session TEXT NOT NULL,
                    investment_amount REAL,
                    risk_profile TEXT,
                    recommended_allocation TEXT,
                    ai_analysis TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_name TEXT NOT NULL,
                    endpoint TEXT,
                    requests_count INTEGER DEFAULT 1,
                    last_used TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(api_name, endpoint)
                )
            """)
            
            self.conn.commit()
            self.logger.info("SQLite database tables initialized/verified successfully.")
        except Exception as e:
            self.logger.error(f"Error initializing SQLite tables: {str(e)}")
    def init_tables_postgresql(self):
        """Initialize PostgreSQL database tables for Indian market"""
        try:
            cursor = self.conn.cursor()
            
            # Market data table for Indian stocks (prices in INR)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,  -- e.g., RELIANCE.NS, NIFTYIT.NS
                    asset_type VARCHAR(20) NOT NULL CHECK (asset_type = 'stock'),  -- Only stocks
                    timestamp TIMESTAMP NOT NULL,
                    open_price DECIMAL(15,8),  -- INR
                    high_price DECIMAL(15,8),  -- INR
                    low_price DECIMAL(15,8),   -- INR
                    close_price DECIMAL(15,8), -- INR
                    volume BIGINT,
                    market_cap DECIMAL(20,2),  -- INR
                    additional_data JSONB,  -- JSON for extra data (e.g., sector info)
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, asset_type, timestamp)
                )
            """)
            
            # Economic indicators table for India
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS economic_indicators (
                    id SERIAL PRIMARY KEY,
                    indicator_name VARCHAR(100) NOT NULL,  -- e.g., india_cpi, rbi_repo_rate
                    value DECIMAL(15,8),
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(indicator_name, timestamp)
                )
            """)
            
            # Portfolio recommendations table for Indian portfolios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_recommendations (
                    id SERIAL PRIMARY KEY,
                    user_session VARCHAR(100) NOT NULL,
                    investment_amount DECIMAL(15,2),  -- INR
                    risk_profile VARCHAR(50),  -- e.g., Conservative, Moderate, Aggressive
                    recommended_allocation JSONB,  -- JSON with Indian stock/sector allocations
                    ai_analysis TEXT,  -- Analysis from AIAnalyzer
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # API usage tracking for yfinance, Finnhub, Gemini
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id SERIAL PRIMARY KEY,
                    api_name VARCHAR(50) NOT NULL,  -- e.g., yfinance, finnhub, gemini
                    endpoint VARCHAR(100),
                    requests_count BIGINT DEFAULT 1,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(api_name, endpoint)
                )
            """)
            
            self.logger.info("PostgreSQL database tables initialized successfully for Indian market")
            cursor.close()
        except Exception as e:
            self.logger.error(f"Error initializing PostgreSQL tables: {str(e)}")
    # In utils/database_manager.py

# ... (after the __init__ and init_tables methods) ...

    def is_available(self):
        """Check if the database connection is available."""
        return self.db_available

    def data_freshness_check(self, symbol, asset_type, max_age_hours=1):
        """Check if data in the database is recent enough."""
        if not self.is_available():
            return False
            
        try:
            cursor = self.conn.cursor()
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            # This query works for both SQLite and PostgreSQL by casting the timestamp
            if self.db_type == "sqlite":
                 query = "SELECT COUNT(*) FROM market_data WHERE symbol = ? AND asset_type = ? AND datetime(created_at) >= datetime(?)"
                 params = (symbol, asset_type, cutoff_time.isoformat())
            else: # PostgreSQL
                 query = "SELECT COUNT(*) FROM market_data WHERE symbol = %s AND asset_type = %s AND created_at >= %s"
                 params = (symbol, asset_type, cutoff_time)

            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            cursor.close()
            return count > 0
            
        except Exception as e:
            self.logger.error(f"Error checking data freshness for {symbol}: {str(e)}")
            return False

    def get_latest_economic_indicator(self, indicator_name, country='India'):
        """Fetch the latest value for a specific economic indicator."""
        if not self.is_available():
            return None
        
        try:
            cursor = self.conn.cursor()
            if self.db_type == "sqlite":
                cursor.execute("""
                    SELECT value FROM economic_indicators 
                    WHERE indicator_name = ? AND country = ? 
                    ORDER BY updated_at DESC LIMIT 1
                """, (indicator_name, country))
            else:
                cursor.execute("""
                    SELECT value FROM economic_indicators 
                    WHERE indicator_name = %s AND country = %s 
                    ORDER BY updated_at DESC LIMIT 1
                """, (indicator_name, country))
            
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Error fetching latest economic indicator '{indicator_name}': {e}")
            return None        
    
    def store_market_data(self, symbol, asset_type, data_df):
        """Store market data in database (works with both SQLite and PostgreSQL)"""
        if not self.db_available:
            self.logger.error("Database not available")
            return False
            
        try:
            if asset_type != 'stock':
                self.logger.error(f"Invalid asset_type: {asset_type}. Only 'stock' allowed for Indian market")
                return False
                
            cursor = self.conn.cursor()
            stored_count = 0
            
            for _, row in data_df.iterrows():
                if self.db_type == "sqlite":
                    cursor.execute("""
                        INSERT OR REPLACE INTO market_data 
                        (symbol, asset_type, timestamp, open_price, high_price, low_price, close_price, volume, additional_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        symbol, 
                        'stock', 
                        str(row.get('timestamp', row.name)),
                        float(str(row.get('open_price', row.get('open', 0)))), 
                        float(str(row.get('high_price', row.get('high', 0)))),
                        float(str(row.get('low_price', row.get('low', 0)))), 
                        float(str(row.get('close_price', row.get('close', 0)))),
                        int(float(str(row.get('volume', 0)))), 
                        None  # No additional data for now
                    ))
                else:  # PostgreSQL
                    cursor.execute("""
                        INSERT INTO market_data 
                        (symbol, asset_type, timestamp, open_price, high_price, low_price, close_price, volume, additional_data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, asset_type, timestamp) DO UPDATE SET
                        open_price = EXCLUDED.open_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        close_price = EXCLUDED.close_price,
                        volume = EXCLUDED,
                        additional_data = EXCLUDED.additional_data
                    """, (
                        symbol, 
                        'stock', 
                        str(row.get('timestamp', row.name)),
                        float(str(row.get('open_price', row.get('open', 0)))), 
                        float(str(row.get('high_price', row.get('high', 0)))),
                        float(str(row.get('low_price', row.get('low', 0)))), 
                        float(str(row.get('close_price', row.get('close', 0)))),
                        int(float(str(row.get('volume', 0)))), 
                        None
                    ))
                stored_count += 1
            
            if self.db_type == "sqlite":
                self.conn.commit()
            
            cursor.close()
            self.logger.info(f"Successfully stored {stored_count} records for {symbol} (stock) in {self.db_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing market data for {symbol}: {str(e)}")
            return False
    
    def get_market_data(self, symbol, asset_type, days_back=30):
        """Retrieve market data for Indian stocks from database"""
        if not self.db_available:
            self.logger.error("Database not available")
            return None
            
        if asset_type != 'stock':
            self.logger.error(f"Invalid asset_type: {asset_type}. Only 'stock' allowed for Indian market")
            return None
            
        try:
            cursor = self.conn.cursor()
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            if self.db_type == "sqlite":
                cursor.execute("""
                    SELECT * FROM market_data 
                    WHERE symbol = ? AND asset_type = ? AND datetime(timestamp) >= datetime(?)
                    ORDER BY timestamp DESC
                """, (symbol, 'stock', cutoff_date.isoformat()))
            else:  # PostgreSQL
                cursor.execute("""
                    SELECT * FROM market_data 
                    WHERE symbol = %s AND asset_type = %s AND timestamp >= %s
                    ORDER BY timestamp DESC
                """, (symbol, 'stock', cutoff_date))
            
            results = cursor.fetchall()
            
            if results and self.db_type == "postgresql":
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                cursor.close()
                return pd.DataFrame([dict(zip(columns, row)) for row in results])
            elif results:
                cursor.close()
                return pd.DataFrame([dict(row) for row in results])
            else:
                cursor.close()
                self.logger.info(f"No market data found for {symbol} (stock)")
                return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving market data for {symbol}: {str(e)}")
            return None
    
    def get_asset_universe(self):
        """Get all available Indian stocks in database"""
        if not self.db_available:
            self.logger.error("Database not available")
            return []
            
        try:
            cursor = self.conn.cursor()
            
            if self.db_type == "sqlite":
                cursor.execute("""
                    SELECT DISTINCT symbol, asset_type, COUNT(*) as data_points
                    FROM market_data
                    WHERE asset_type = 'stock'
                    GROUP BY symbol, asset_type
                    ORDER BY symbol
                """)
            else:  # PostgreSQL
                cursor.execute("""
                    SELECT DISTINCT symbol, asset_type, COUNT(*) as data_points
                    FROM market_data
                    WHERE asset_type = 'stock'
                    GROUP BY symbol, asset_type
                    ORDER BY symbol
                """)
            
            results = cursor.fetchall()
            
            if self.db_type == "sqlite":
                cursor.close()
                return [dict(row) for row in results]
            else:
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                cursor.close()
                return [dict(zip(columns, row)) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting asset universe: {str(e)}")
            return []
    
    # In utils/database_manager.py
# FIX: Changed parameter name from 'allocation' to 'recommended_allocation'
def store_portfolio_recommendation(self, user_session, investment_amount, risk_profile, recommended_allocation, ai_analysis):
    """Store portfolio recommendation for Indian stocks"""
    if not self.db_available:
        self.logger.error("Database not available")
        return False
        
    try:
        cursor = self.conn.cursor()
        
        # Use ai_analysis as the parameter for the analysis text
        allocation_json = json.dumps(recommended_allocation, default=str)

        if self.db_type == "sqlite":
            cursor.execute("""
                INSERT INTO portfolio_recommendations 
                (user_session, investment_amount, risk_profile, recommended_allocation, ai_analysis)
                VALUES (?, ?, ?, ?, ?)
            """, (user_session, investment_amount, risk_profile, allocation_json, ai_analysis))
            self.conn.commit()
        else:  # PostgreSQL
            cursor.execute("""
                INSERT INTO portfolio_recommendations 
                (user_session, investment_amount, risk_profile, recommended_allocation, ai_analysis)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_session, investment_amount, risk_profile, allocation_json, ai_analysis))
        
        cursor.close()
        self.logger.info(f"Stored portfolio recommendation for session {user_session}")
        return True
        
    except Exception as e:
        self.logger.error(f"Error storing portfolio recommendation: {str(e)}")
        return False
    
    def data_freshness_check(self, symbol, asset_type, max_age_hours=1):
        """Check if data is fresh enough for Indian stocks"""
        if not self.db_available:
            self.logger.error("Database not available")
            return False
            
        if asset_type != 'stock':
            self.logger.error(f"Invalid asset_type: {asset_type}. Only 'stock' allowed for Indian market")
            return False
            
        try:
            cursor = self.conn.cursor()
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            if self.db_type == "sqlite":
                cursor.execute("""
                    SELECT COUNT(*) FROM market_data 
                    WHERE symbol = ? AND asset_type = ? AND datetime(created_at) >= datetime(?)
                """, (symbol, 'stock', cutoff_time.isoformat()))
            else:  # PostgreSQL
                cursor.execute("""
                    SELECT COUNT(*) FROM market_data 
                    WHERE symbol = %s AND asset_type = %s AND created_at >= %s
                """, (symbol, 'stock', cutoff_time))
            
            count = cursor.fetchone()[0]
            cursor.close()
            return count > 0
            
        except Exception as e:
            self.logger.error(f"Error checking data freshness for {symbol}: {str(e)}")
            return False
    
    # In utils/database_manager.py
    def get_database_info(self):
        """Get database information for display"""
        if not self.db_available:
            return {"type": "none", "status": "unavailable"}
        
        info = {
            "type": self.db_type,
            "status": "connected",
            "market_records": 0,
            "portfolio_records": 0,
            "economic_records": 0,
            "api_usage_records": 0,
            "file_path": "data/portfolio_manager.db" if self.db_type == "sqlite" else "PostgreSQL"
        }
        
        try:
            cursor = self.conn.cursor()
            
            # Use try-except for each query to handle missing tables gracefully
            try:
                cursor.execute("SELECT COUNT(*) FROM market_data")
                info["market_records"] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                self.logger.warning("market_data table not found.")

            try:
                cursor.execute("SELECT COUNT(*) FROM portfolio_recommendations")
                info["portfolio_records"] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                self.logger.warning("portfolio_recommendations table not found.")

            try:
                cursor.execute("SELECT COUNT(*) FROM economic_indicators")
                info["economic_records"] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                self.logger.warning("economic_indicators table not found.")

            try:
                cursor.execute("SELECT COUNT(*) FROM api_usage")
                info["api_usage_records"] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                self.logger.warning("api_usage table not found.")
            
            cursor.close()
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting database info: {str(e)}")
            info["status"] = "error"
            info["error"] = str(e)
            return info
            
        
    
    def is_available(self):
        """Check if database is available"""
        return self.db_available
    
    def close_connection(self):
        """Close database connection"""
        if self.conn and self.db_available:
            self.conn.close()
            self.logger.info(f"{self.db_type.title()} database connection closed")
    # In utils/database_manager.py

# ... (after all other methods in the class) ...

    def store_portfolio_recommendation(self, user_session, investment_amount, risk_profile, recommended_allocation, ai_analysis):
        """Store portfolio recommendation for Indian stocks"""
        if not self.is_available():
            self.logger.error("Database not available, cannot store portfolio recommendation.")
            return False
            
        try:
            cursor = self.conn.cursor()
            
            # Convert allocation dictionary to a JSON string for storage
            allocation_json = json.dumps(recommended_allocation, default=str)

            if self.db_type == "sqlite":
                cursor.execute("""
                    INSERT INTO portfolio_recommendations 
                    (user_session, investment_amount, risk_profile, recommended_allocation, ai_analysis)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_session, float(investment_amount), risk_profile, allocation_json, ai_analysis))
            else:  # PostgreSQL
                cursor.execute("""
                    INSERT INTO portfolio_recommendations 
                    (user_session, investment_amount, risk_profile, recommended_allocation, ai_analysis)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_session, float(investment_amount), risk_profile, allocation_json, ai_analysis))
            
            if self.db_type == "sqlite":
                self.conn.commit()
            
            cursor.close()
            self.logger.info(f"Stored portfolio recommendation for session {user_session}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing portfolio recommendation: {str(e)}")
            if self.db_type == "sqlite":
                self.conn.rollback()
            return False

    def get_database_info(self):
        """Get database information for display"""
        if not self.is_available():
            return {"type": "none", "status": "unavailable"}
        
        info = {
            "type": self.db_type,
            "status": "connected",
            "market_records": 0,
            "portfolio_records": 0,
            "file_path": "data/portfolio_manager.db" if self.db_type == "sqlite" else "PostgreSQL"
        }
        
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM market_data")
            info["market_records"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM portfolio_recommendations")
            info["portfolio_records"] = cursor.fetchone()[0]
            
            cursor.close()
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting database info: {str(e)}")
            info["status"] = "error"
            info["error"] = str(e)
            return info

    # In utils/database_manager.py

# ... (after your other methods like is_available(), store_portfolio_recommendation(), etc.)

    def get_database_info(self):
        """Get database information for display."""
        if not self.is_available():
            return {"type": "none", "status": "unavailable"}
        
        info = {
            "type": self.db_type,
            "status": "connected",
            "market_records": 0,
            "portfolio_records": 0,
            "file_path": "data/portfolio_manager.db" if self.db_type == "sqlite" else "PostgreSQL"
        }
        
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM market_data")
            info["market_records"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM portfolio_recommendations")
            info["portfolio_records"] = cursor.fetchone()[0]
            
            cursor.close()
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting database info: {str(e)}")
            info["status"] = "error"
            info["error"] = str(e)
            return info

    def get_asset_universe(self):
        """Retrieve all unique assets and their data point counts from the database."""
        if not self.is_available():
            return []
            
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT symbol, asset_type, COUNT(*) as data_points
                FROM market_data
                GROUP BY symbol, asset_type
                ORDER BY symbol
            """
            cursor.execute(query)
            # Convert list of Row objects to list of dicts
            assets = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            return assets
        except Exception as e:
            self.logger.error(f"Error retrieving asset universe: {str(e)}")
            return []        
    