import json
import os
from datetime import datetime, timedelta
from typing import Optional

import google.generativeai as genai
import pandas as pd
import requests
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
                self.model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
                print("Gemini model initialized successfully.")
            except Exception as e:
                print(f"Error initializing Gemini model: {str(e)}")
                self.model = None

    def _get_ticker_symbol(self, company: str) -> Optional[str]:
        """Enhanced global company ticker lookup with better search."""

        # Comprehensive ticker mapping
        ticker_map = {
            # US Companies
            "APPLE": "AAPL",
            "MICROSOFT": "MSFT",
            "TESLA": "TSLA",
            "AMAZON": "AMZN",
            "GOOGLE": "GOOGL",
            "META": "META",
            "MCDONALDS": "MCD",
            "MCD": "MCD",
            "MCDONALD": "MCD",
            # Indian Companies (NSE)
            "TCS": "TCS.NS",
            "TATA CONSULTANCY SERVICES": "TCS.NS",
            "ITC": "ITC.NS",
            "ITC LIMITED": "ITC.NS",
            "VEDANTA": "VEDL.NS",
            "VEDANTA LIMITED": "VEDL.NS",
            "RELIANCE": "RELIANCE.NS",
            "RELIANCE INDUSTRIES": "RELIANCE.NS",
            "INFOSYS": "INFY.NS",
            "WIPRO": "WIPRO.NS",
            "HDFC BANK": "HDFCBANK.NS",
            "ICICI BANK": "ICICIBANK.NS",
            "STATE BANK OF INDIA": "SBIN.NS",
            "SBI": "SBIN.NS",
            # Korean Companies
            "SAMSUNG": "005930.KS",
            "SAMSUNG ELECTRONICS": "005930.KS",
            "LG": "066570.KS",
            "LG ELECTRONICS": "066570.KS",
            "HYUNDAI": "005380.KS",
            "HYUNDAI MOTOR": "005380.KS",
            # Japanese Companies
            "TOYOTA": "7203.T",
            "TOYOTA MOTOR": "7203.T",
            "SONY": "6758.T",
            "SONY CORPORATION": "6758.T",
            "NINTENDO": "7974.T",
            "HONDA": "7267.T",
            # European Companies
            "VOLKSWAGEN": "VOW3.DE",
            "BMW": "BMW.DE",
            "MERCEDES": "MBG.DE",
            "SAP": "SAP.DE",
        }

        try:
            # Clean and normalize input
            clean_name = company.upper().strip()
            clean_name = clean_name.replace(" LIMITED", "").replace(" LTD", "")
            clean_name = clean_name.replace(" CORP", "").replace(" CORPORATION", "")
            clean_name = clean_name.replace(" INC", "").replace(" COMPANY", "")

            # Direct lookup
            if clean_name in ticker_map:
                ticker = ticker_map[clean_name]
                if self._validate_ticker(ticker):
                    print(f"Found ticker: {ticker}")
                    return ticker

            # Try partial matches
            for key, ticker in ticker_map.items():
                if clean_name in key or key in clean_name:
                    if self._validate_ticker(ticker):
                        print(f"Found ticker via partial match: {ticker}")
                        return ticker

            # If input already looks like a ticker, validate it
            if any(suffix in company for suffix in [".NS", ".BO", ".T", ".KS", ".DE"]):
                if self._validate_ticker(company):
                    return company

            # Try the original input as ticker
            if self._validate_ticker(clean_name):
                return clean_name

            print(f"No ticker found for company: {company}")
            return None

        except Exception as e:
            print(f"Error in ticker lookup: {str(e)}")
            return None

    def _validate_ticker(self, ticker: str) -> bool:
        """Validate if ticker exists and has data."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            # Check if ticker has essential data
            return (
                info
                and (info.get("regularMarketPrice") or info.get("currentPrice"))
                and info.get("marketCap")
            )
        except:
            return False

    def fetch_financial_data(self):
        """Fetch and format financial data with proper currency handling."""
        if not self.ticker_symbol:
            return {
                "error": f"No valid ticker found for {self.company}",
                "company": self.company,
                "timestamp": datetime.now().isoformat(),
            }

        try:
            ticker = yf.Ticker(self.ticker_symbol)
            info = ticker.info

            # Get current price (try multiple fields)
            current_price = (
                info.get("regularMarketPrice")
                or info.get("currentPrice")
                or info.get("previousClose", 0)
            )

            # Get market cap and currency
            market_cap = info.get("marketCap")
            currency = info.get("currency", "USD")

            # Exchange mapping
            exchange_map = {
                "NSI": "NSE",
                "NSE": "NSE",
                "BSE": "BSE",
                "BOM": "BSE",
                "NMS": "NASDAQ",
                "NGM": "NASDAQ",
                "NYQ": "NYSE",
                "NYE": "NYSE",
                "KSC": "KRX",
                "KOE": "KRX",
                "JPX": "TSE",
                "TYO": "TSE",
                "GER": "XETRA",
                "GTY": "XETRA",
            }

            # Accurate currency conversion rates (you might want to use a real API)
            fx_rates = {
                "INR": 0.012,  # 1 INR ≈ 0.012 USD
                "JPY": 0.007,  # 1 JPY ≈ 0.007 USD
                "KRW": 0.00075,  # 1 KRW ≈ 0.00075 USD
                "EUR": 1.08,  # 1 EUR ≈ 1.08 USD
                "USD": 1.0,
            }

            financial_data = {
                "company": self.company,
                "ticker": self.ticker_symbol,
                "current_price": (
                    round(float(current_price), 2) if current_price else None
                ),
                "price_change_percent": round(
                    float(info.get("regularMarketChangePercent", 0)), 2
                ),
                "market_cap": {
                    "value": market_cap,
                    "currency": currency,
                    "usd_value": (
                        round(market_cap * fx_rates.get(currency, 1.0), 2)
                        if market_cap
                        else None
                    ),
                    "formatted": self._format_market_cap(market_cap, currency),
                },
                "exchange": exchange_map.get(
                    info.get("exchange", ""), info.get("exchange", "N/A")
                ),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "pe_ratio": info.get("forwardPE") or info.get("trailingPE"),
                "volume": info.get("volume"),
                "avg_volume": info.get("averageVolume"),
                "timestamp": datetime.now().isoformat(),
            }

            return financial_data

        except Exception as e:
            print(f"Error fetching financial data: {str(e)}")
            return {
                "error": str(e),
                "company": self.company,
                "ticker": self.ticker_symbol,
                "timestamp": datetime.now().isoformat(),
            }

    def _format_market_cap(self, value, currency):
        """Format market cap with proper currency symbols and regional conventions."""
        if not value:
            return "N/A"

        currency_symbols = {
            "USD": "$",
            "INR": "₹",
            "JPY": "¥",
            "KRW": "₩",
            "EUR": "€",
            "GBP": "£",
        }

        symbol = currency_symbols.get(currency, currency + " ")

        # Handle different regional conventions
        if currency == "INR":
            # Indian numbering system (Crores, Lakhs)
            if value >= 1e7:  # 1 Crore
                return f"{symbol}{value/1e7:.2f} Cr"
            elif value >= 1e5:  # 1 Lakh
                return f"{symbol}{value/1e5:.2f} L"
        elif currency == "KRW":
            # Korean Won (often in billions)
            if value >= 1e12:
                return f"{symbol}{value/1e12:.2f}조"  # Trillion in Korean
            elif value >= 1e8:
                return f"{symbol}{value/1e8:.2f}억"  # Hundred million in Korean
        elif currency == "JPY":
            # Japanese Yen
            if value >= 1e12:
                return f"{symbol}{value/1e12:.2f}兆"  # Trillion in Japanese
            elif value >= 1e8:
                return f"{symbol}{value/1e8:.2f}億"  # Hundred million in Japanese

        # Standard Western format (USD, EUR, etc.)
        if value >= 1e12:
            return f"{symbol}{value/1e12:.2f}T"
        elif value >= 1e9:
            return f"{symbol}{value/1e9:.2f}B"
        elif value >= 1e6:
            return f"{symbol}{value/1e6:.2f}M"
        elif value >= 1e3:
            return f"{symbol}{value/1e3:.2f}K"

        return f"{symbol}{value:,.0f}"

    def _generate_analysis(self, financial_data):
        """Generate financial analysis using Gemini."""
        if not self.model or financial_data.get("error"):
            return "Financial analysis not available"

        try:
            prompt = f"""Analyze the financial data for {self.company}:

            Current Price: {financial_data.get('current_price', 'N/A')}
            Price Change: {financial_data.get('price_change_percent', 'N/A')}%
            Market Cap: {financial_data.get('market_cap', {}).get('formatted', 'N/A')}
            52-Week Range: {financial_data.get('52_week_low', 'N/A')} - {financial_data.get('52_week_high', 'N/A')}
            P/E Ratio: {financial_data.get('pe_ratio', 'N/A')}
            Volume: {financial_data.get('volume', 'N/A')}

            Provide a brief analysis covering:
            1. Current valuation assessment
            2. Price momentum and trends
            3. Key financial health indicators
            4. Investment perspective (bullish/bearish/neutral)
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
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(financial_data, f, indent=4, ensure_ascii=False)
            print(f"Financial data saved to {output_path}")
        except Exception as e:
            print(f"Error saving financial data: {str(e)}")

    def run(self):
        """Execute the agent's tasks."""
        financial_data = self.fetch_financial_data()
        if financial_data and not financial_data.get("error"):
            # Add analysis if Gemini is available
            if self.model:
                analysis = self._generate_analysis(financial_data)
                financial_data["analysis"] = analysis

            self.save_data(financial_data)
        elif financial_data.get("error"):
            print(f"Financial analysis failed: {financial_data['error']}")
            self.save_data(financial_data)  # Save error info too

        return financial_data


if __name__ == "__main__":
    agent = FinancialAnalystAgent(company="Samsung")
    result = agent.run()
    print(json.dumps(result, indent=2))
