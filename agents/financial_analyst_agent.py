import json
import os
from datetime import datetime, timedelta
from typing import Optional

import google.generativeai as genai
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv


class FinancialAnalystAgent:
    def __init__(self, company, output_dir="data"):
        self.company = company
        self.ticker_symbol = self._get_ticker_symbol(company)
        self.output_dir = output_dir
        load_dotenv()
        self.setup_models()

    def setup_models(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
                print("Gemini model initialized successfully.")
            except Exception as e:
                print(f"Error initializing Gemini model: {str(e)}")
                self.model = None

    def _get_ticker_symbol(self, company: str) -> Optional[str]:
        """Dynamic global company ticker lookup."""
        # Common stock symbols mapping
        common_tickers = {
            "ITC": "ITC.NS",
            "VEDANTA": "VEDL.NS",
            "TCS": "TCS.NS",
            "TESLA": "TSLA",
            "APPLE": "AAPL",
            "MICROSOFT": "MSFT"
        }

        try:
            # Clean input
            clean_name = company.upper().replace("LIMITED", "").replace("LTD", "").strip()
            
            # Check common tickers first
            if clean_name in common_tickers:
                ticker = yf.Ticker(common_tickers[clean_name])
                if ticker.info:
                    print(f"Found ticker: {common_tickers[clean_name]}")
                    return common_tickers[clean_name]

            # Try direct input if it contains exchange suffix
            if any(suffix in company for suffix in ['.NS', '.BO', '.T', '.KS']):
                ticker = yf.Ticker(company)
                if ticker.info:
                    print(f"Found ticker: {company}")
                    return company

            # Try yfinance search
            try:
                ticker = yf.Ticker(clean_name)
                if ticker.info and 'regularMarketPrice' in ticker.info:
                    print(f"Found ticker: {clean_name}")
                    return clean_name
            except:
                pass

            return None

        except Exception as e:
            print(f"Error in ticker lookup: {str(e)}")
            return None

    def fetch_financial_data(self):
        """Fetch and format financial data with proper currency handling."""
        try:
            ticker = yf.Ticker(self.ticker_symbol)
            info = ticker.info

            # Get market cap and currency
            market_cap = info.get('marketCap')
            currency = info.get('currency', 'USD')

            # Standardize exchange names
            exchange_map = {
                'NSI': 'NSE',  # Fix for Indian National Stock Exchange
                'BSE': 'BSE'   # Bombay Stock Exchange
            }

            # More accurate currency conversion rates
            fx_rates = {
                'INR': 0.012075,  # 1 INR = 0.012075 USD (as of current rate)
                'JPY': 0.0068,    # 1 JPY = 0.0068 USD
                'KRW': 0.00075,   # 1 KRW = 0.00075 USD
                'EUR': 1.07,      # 1 EUR = 1.07 USD
                'USD': 1.0
            }

            exchange = exchange_map.get(info.get('exchange', ''), info.get('exchange', 'N/A'))

            financial_data = {
                "company": self.company,
                "ticker": self.ticker_symbol,
                "current_price": round(float(info.get('regularMarketPrice', 0)), 2),
                "price_change_percent": round(float(info.get('regularMarketChangePercent', 0)), 2),
                "market_cap": {
                    "value": market_cap,
                    "currency": currency,
                    "usd_value": round(market_cap * fx_rates.get(currency, 1.0), 2) if market_cap else None,
                    "formatted": self._format_market_cap(market_cap, currency)
                },
                "exchange": exchange,
                "timestamp": datetime.now().isoformat()
            }

            return financial_data

        except Exception as e:
            print(f"Error fetching financial data: {str(e)}")
            return {}

    def _format_market_cap(self, value, currency):
        """Format market cap with proper currency symbols."""
        if not value:
            return "N/A"

        currency_symbols = {
            'USD': '$',
            'INR': '₹',
            'JPY': '¥',
            'KRW': '₩',
            'EUR': '€'
        }

        symbol = currency_symbols.get(currency, currency + ' ')

        # Handle Indian values in Crores
        if currency == 'INR':
            if value >= 1e7:
                return f"{symbol}{value/1e7:.2f} Cr"
            elif value >= 1e5:
                return f"{symbol}{value/1e5:.2f} Lakh"
        else:
            if value >= 1e12:
                return f"{symbol}{value/1e12:.2f}T"
            elif value >= 1e9:
                return f"{symbol}{value/1e9:.2f}B"
            elif value >= 1e6:
                return f"{symbol}{value/1e6:.2f}M"

        return f"{symbol}{value:,.2f}"

    def _calculate_ratios(self, balance_sheet, income_stmt):
        """Calculate important financial ratios."""
        try:
            return {
                "quick_ratio": self._calculate_quick_ratio(balance_sheet),
                "debt_to_equity": self._calculate_debt_to_equity(balance_sheet),
                "profit_margin": self._calculate_profit_margin(income_stmt),
            }
        except Exception as e:
            print(f"Error calculating ratios: {str(e)}")
            return {}

    def _generate_analysis(self, ticker):
        """Generate analysis using Gemini."""
        if not self.model:
            return "Analysis not available"

        try:
            info = ticker.info
            prompt = f"""Analyze {self.company}'s financial position based on:
            - Current Price: ${info.get('currentPrice', 'N/A')}
            - Market Cap: ${info.get('marketCap', 'N/A')}
            - P/E Ratio: {info.get('forwardPE', 'N/A')}
            - 52W Range: ${info.get('fiftyTwoWeekLow', 'N/A')} - ${info.get('fiftyTwoWeekHigh', 'N/A')}

            Provide a brief analysis of the company's financial health and market position.
            """

            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating analysis: {str(e)}")
            return "Analysis generation failed"

    def save_data(self, financial_data):
        """Save financial data to JSON file."""
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "financial_data.json")
        try:
            with open(output_path, "w") as f:
                json.dump(financial_data, f, indent=4)
            print(f"Financial data saved to {output_path}")
        except Exception as e:
            print(f"Error saving financial data: {str(e)}")

    def run(self):
        """Execute the agent's tasks."""
        financial_data = self.fetch_financial_data()
        if financial_data:
            self.save_data(financial_data)
        return financial_data


if __name__ == "__main__":
    agent = FinancialAnalystAgent(company="Samsung")
    agent.run()
