import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai

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

    def _get_ticker_symbol(self, company):
        """Enhanced company to ticker symbol mapping."""
        ticker_map = {
            "Samsung": "005930.KS",  # Korea Exchange
            "Tesla": "TSLA",         # NASDAQ
            "Toyota": "7203.T",      # Tokyo Exchange
            "Volkswagen": "VOW3.DE"  # German Exchange
        }
        return ticker_map.get(company)

    def fetch_financial_data(self):
        """Fetch comprehensive financial data."""
        try:
            ticker = yf.Ticker(self.ticker_symbol)

            # Basic info
            info = ticker.info

            # Historical data
            hist = ticker.history(period="1y")

            # Financial statements
            balance_sheet = ticker.balance_sheet
            income_stmt = ticker.income_stmt
            cash_flow = ticker.cashflow

            # Calculate key metrics
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            price_change = ((current_price - prev_price) / prev_price) * 100

            financial_data = {
                "company": self.company,
                "ticker": self.ticker_symbol,
                "current_price": round(current_price, 2),
                "price_change_percent": round(price_change, 2),
                "market_cap": info.get("marketCap"),
                "currency": info.get("currency"),
                "exchange": info.get("exchange"),
                "key_metrics": {
                    "pe_ratio": info.get("forwardPE"),
                    "dividend_yield": info.get("dividendYield"),
                    "52w_high": info.get("fiftyTwoWeekHigh"),
                    "52w_low": info.get("fiftyTwoWeekLow")
                },
                "financial_ratios": self._calculate_ratios(balance_sheet, income_stmt),
                "analysis": self._generate_analysis(ticker),
                "timestamp": datetime.now().isoformat()
            }

            return financial_data
        except Exception as e:
            print(f"Error fetching financial data: {str(e)}")
            return {}

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