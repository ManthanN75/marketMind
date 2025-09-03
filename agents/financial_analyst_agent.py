import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional

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
                self.model = genai.GenerativeModel('gemini-pro')
                print("Gemini model initialized successfully.")
            except Exception as e:
                print(f"Error initializing Gemini model: {str(e)}")
                self.model = None

    def _get_ticker_symbol(self, company: str) -> Optional[str]:
        """Map company names to their ticker symbols."""
        ticker_map = {
            "Bayerische Motoren Werke AG": "BMW.DE",
            "BMW": "BMW.DE",
            # India
            "Maruti Suzuki": "MARUTI.NS",
            "Vedanta": "VEDL.NS",
            "ITC": "ITC.NS",
            "Bajaj": "BAJFINANCE.NS",
            
            # Global
            "Tesla": "TSLA",
            "LG": "066570.KS",
            "Hyundai": "005380.KS",
            "Honda": "7267.T",
            "Boeing": "BA",
            "Apple": "AAPL",
            "Lenovo": "0992.HK"
        }
        
        # Clean company name
        company_clean = company.upper().replace("AG", "").strip()
        
        # Try direct mapping first
        if company in ticker_map:
            return ticker_map[company]
        
        try:
            # Try yfinance search
            ticker = yf.Ticker(company_clean)
            if ticker.info and 'symbol' in ticker.info:
                return ticker.info['symbol']
            
            # Try common variations
            variations = [
                company_clean,
                company_clean + ".DE",  # German stocks
                company_clean + ".F"     # Frankfurt exchange
            ]
            
            for variation in variations:
                try:
                    ticker = yf.Ticker(variation)
                    info = ticker.info
                    if info and 'regularMarketPrice' in info:
                        return variation
                except:
                    continue
                
            return None
        except Exception as e:
            print(f"Error finding ticker: {str(e)}")
            return None

    def fetch_financial_data(self):
        """Fetch comprehensive financial data."""
        try:
            ticker = yf.Ticker(self.ticker_symbol)

            # Get market cap and currency info
            market_cap = ticker.info.get('marketCap')
            currency = ticker.info.get("currency", "USD")
            # Currency conversion rates (can be updated with real-time forex data)
            forex_rates = {
                "JPY": 0.0068,  # 1 JPY = 0.0068 USD
                "KRW": 0.00075, # 1 KRW = 0.00075 USD
                "EUR": 1.07     # 1 EUR = 1.07 USD
            }

            # Convert market cap to USD if needed
            if currency != "USD" and currency in forex_rates:
                usd_market_cap = market_cap * forex_rates[currency]
            else:
                usd_market_cap = market_cap

            # Get current price and calculate change
            current_price = ticker.fast_info.last_price
            hist = ticker.history(period="2d")
            price_change = 0
            if not hist.empty and len(hist) >= 2:
                prev_close = hist['Close'].iloc[-2]
                price_change = ((current_price - prev_close) / prev_close) * 100

            financial_data = {
                "company": self.company,
                "ticker": self.ticker_symbol,
                "current_price": round(float(current_price), 2),
                "price_change_percent": round(float(price_change), 2),
                "market_cap": {
                    "value": market_cap,
                    "currency": currency,
                    "usd_value": usd_market_cap,
                    "formatted": f"${usd_market_cap/1e9:.2f}B USD"
                },
                "exchange": ticker.info.get("exchange", "N/A"),
                "timestamp": datetime.now().isoformat()
            }
            return financial_data
        except Exception as e:
            print(f"Error fetching financial data: {str(e)}")
            return {}

    def _format_market_cap(self, market_cap):
        """Format market cap into readable format based on listing currency."""
        try:
            if not market_cap:
                return "N/A"

            # Handle Japanese stocks (listed in JPY)
            if self.ticker_symbol.endswith('.T'):
                if market_cap >= 1e12:  # Trillion JPY
                    return f"¥{market_cap/1e12:.2f}T"
                elif market_cap >= 1e9:  # Billion JPY
                    return f"¥{market_cap/1e9:.2f}B"
                elif market_cap >= 1e6:  # Million JPY
                    return f"¥{market_cap/1e6:.2f}M"
            else:
                # For USD and other currencies
                if market_cap >= 1e12:
                    return f"${market_cap/1e12:.2f}T"
                elif market_cap >= 1e9:
                    return f"${market_cap/1e9:.2f}B"
                elif market_cap >= 1e6:
                    return f"${market_cap/1e6:.2f}M"

            return f"${market_cap:,.2f}"
        except Exception:
            return "N/A"

    def _calculate_ratios(self, balance_sheet, income_stmt):
        """Calculate important financial ratios."""
        try:
            return {
                "quick_ratio": self._calculate_quick_ratio(balance_sheet),
                "debt_to_equity": self._calculate_debt_to_equity(balance_sheet),
                "profit_margin": self._calculate_profit_margin(income_stmt)
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