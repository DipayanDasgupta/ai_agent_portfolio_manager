# test_components.py

import unittest
import pandas as pd
import os
import sys
from dotenv import load_dotenv

# Load environment variables and set up path
load_dotenv()
# NEW, CORRECTED CODE
# Add the project's root directory to the Python path
# This allows for absolute imports like 'from utils.data_fetcher import ...'
# and also lets the utils module perform its own relative imports correctly.
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import all the utility classes we want to test
# NEW, CORRECTED ABSOLUTE IMPORTS
from utils.data_fetcher import DataFetcher
from utils.ai_analyzer import AIAnalyzer
from utils.portfolio_optimizer import PortfolioOptimizer
from utils.risk_calculator import RiskCalculator
from utils.database_manager import DatabaseManager
from utils.fallback_data_provider import FallbackDataProvider

class TestPortfolioManagerComponents(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up all components once for all tests."""
        print("\n--- Initializing Components for Testing ---")
        cls.data_fetcher = DataFetcher()
        cls.ai_analyzer = AIAnalyzer()
        cls.optimizer = PortfolioOptimizer()
        cls.risk_calc = RiskCalculator(symbols=['RELIANCE.NS', 'TCS.NS'])
        cls.db_manager = DatabaseManager()
        cls.fallback_provider = FallbackDataProvider()
        print("--- Components Initialized ---\n")

    def test_01_data_fetcher_real_data(self):
        """
        Test 1: DataFetcher - Verifies fetching of REAL-TIME stock data.
        This is the most important test to check your data source.
        """
        print("\n--- Testing DataFetcher for REAL data ---")
        symbol = 'RELIANCE.NS'
        print(f"Attempting to fetch live data for {symbol}...")
        df = self.data_fetcher.get_stock_data(symbol, period='5d')

        # Test 1: Did we get a DataFrame?
        self.assertIsInstance(df, pd.DataFrame, "get_stock_data should return a DataFrame.")
        
        # Test 2: Is the DataFrame non-empty?
        self.assertFalse(df.empty, f"Data fetched for {symbol} should not be empty.")
        
        # Test 3: Does it have the required columns?
        expected_cols = ['open', 'high', 'low', 'close', 'volume']
        self.assertTrue(all(col in df.columns for col in expected_cols), f"DataFrame missing required columns: {expected_cols}")
        
        # Test 4: THE CRITICAL TEST - Is the data real or synthetic?
        # We check if the 'source' column exists, which our fallback provider adds.
        # Real data from yfinance will NOT have this column.
        is_synthetic = 'source' in df.columns and df['source'].iloc[0] == 'synthetic'
        self.assertFalse(is_synthetic, f"CRITICAL: Data for {symbol} is SYNTHETIC. Real-time fetch failed.")
        
        print(f"✅ PASSED: Successfully fetched REAL data for {symbol}.")
        print(df.tail(2))

    def test_02_fallback_provider(self):
        """
        Test 2: FallbackDataProvider - Verifies generation of SYNTHETIC data.
        """
        print("\n--- Testing FallbackDataProvider for SYNTHETIC data ---")
        symbol = 'TCS.NS'
        df = self.fallback_provider.generate_stock_data(symbol)
        
        self.assertFalse(df.empty, "Fallback provider should generate a non-empty DataFrame.")
        
        # This is the key check: synthetic data MUST be tagged.
        self.assertIn('source', df.columns, "Synthetic data must have a 'source' column.")
        self.assertEqual(df['source'].iloc[0], 'synthetic', "Source column should be marked 'synthetic'.")
        
        print("✅ PASSED: Fallback provider correctly generates tagged synthetic data.")

    def test_03_ai_analyzer(self):
        """
        Test 3: AIAnalyzer - Verifies connection and basic analysis from Gemini.
        """
        print("\n--- Testing AIAnalyzer (Gemini API) ---")
        self.assertIsNotNone(self.ai_analyzer.model, "AI Analyzer (Gemini) model should be initialized.")
        
        prompt = "Provide a brief, one-sentence outlook for the Indian IT sector."
        response = self.ai_analyzer.get_market_analysis(prompt)
        
        self.assertIsNotNone(response, "AI response should not be None.")
        self.assertIsInstance(response, str, "AI response should be a string.")
        self.assertNotIn("unavailable", response.lower(), "AI response should not indicate service is unavailable.")
        self.assertNotIn("error", response.lower(), "AI response should not contain an error message.")
        
        print("✅ PASSED: AI Analyzer successfully received a response from Gemini.")
        print(f"Gemini Response Snippet: '{response[:80]}...'")

    # In test_components.py -> test_04_portfolio_optimizer

    def test_04_portfolio_optimizer(self):
        """
        Test 4: PortfolioOptimizer - Verifies that portfolio optimization runs without errors.
        """
        print("\n--- Testing PortfolioOptimizer ---")
        symbols = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS']
        
        # --- START OF FIX ---
        # Fetch data robustly and check for failures before proceeding.
        data = {}
        for s in symbols:
            df = self.data_fetcher.get_stock_data(s, period='3mo')
            # Only add to data if the fetch was successful
            if df is not None and not df.empty:
                data[s] = df['close']
            else:
                self.fail(f"Data fetching failed for symbol {s} during optimizer test. Cannot proceed.")
        # --- END OF FIX ---

        returns_data = pd.DataFrame(data).dropna()
        self.assertGreater(len(returns_data), 30, "Not enough historical data for optimization test.")
        
        result = self.optimizer.optimize_portfolio(returns_data, optimization_type='sharpe')
        
        self.assertIsNotNone(result, "Optimization should return a result dictionary.")
        self.assertTrue(result.get('success'), f"Optimization should be successful. Reason: {result.get('message', 'N/A')}")
        self.assertIn('weights', result, "Result should contain portfolio weights.")
        self.assertAlmostEqual(sum(result['weights'].values()), 1.0, places=4, msg="Weights should sum to 1.")
        
        print("✅ PASSED: Portfolio optimization completed successfully.")
        print(f"Optimal Weights: {result['weights']}")

    def test_05_database_manager(self):
        """
        Test 5: DatabaseManager - Verifies database connection and basic operations.
        """
        print("\n--- Testing DatabaseManager ---")
        self.assertTrue(self.db_manager.is_available(), "Database connection should be available.")

        # Test storing and retrieving a portfolio
        test_session = "test_run_123"
        test_alloc = {'RELIANCE.NS': 0.5, 'TCS.NS': 0.5}
        test_analysis = "Test analysis text."
        
        stored = self.db_manager.store_portfolio_recommendation(
            user_session=test_session,
            investment_amount=100000,
            risk_profile="TEST",
            recommended_allocation=test_alloc,
            ai_analysis=test_analysis
        )
        self.assertTrue(stored, "Storing a portfolio recommendation should succeed.")
        
        print("✅ PASSED: DatabaseManager connected and basic operations are working.")


if __name__ == '__main__':
    # This allows running the test script directly
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)