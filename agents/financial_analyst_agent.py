import yfinance as yf
import json
import os
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

class FinancialAnalystAgent:
    def __init__(self, company, output_dir="data"):
        self.company = company
        self.ticker_symbol = self._get_ticker_symbol(company)
        self.output_dir = output_dir
        # Load environment variables for Gemini API
        load_dotenv()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-pro") if self.gemini_api_key else None

    def _get_ticker_symbol(self, company):
        """Map company name to ticker symbol."""
        ticker_map = {
            "Tesla": "TSLA",
            "Samsung": "005930.KS"  # KRX for Samsung
        }
        return ticker_map.get(company, "TSLA")  # Default to TSLA for testing

    def fetch_financial_data(self):
        """Fetch stock data using yfinance."""
        try:
            ticker = yf.Ticker(self.ticker_symbol)
            info = ticker.info
            history = ticker.history(period="1d")

            financial_data = {
                "company": self.company,
                "ticker": self.ticker_symbol,
                "exchange": info.get("exchange", "N/A"),
                "stock_price": round(info.get("regularMarketPrice", 0.0), 2),
                "pe_ratio": round(info.get("forwardPE", 0.0), 2),
                "volume": int(history["Volume"].iloc[-1]) if not history.empty else 0,
                "timestamp": datetime.now().isoformat()
            }

            # Optional: Use Gemini Pro to summarize financial data
            if self.model:
                prompt = f"Summarize the financial outlook for {self.company} based on: P/E ratio {financial_data['pe_ratio']}, stock price ${financial_data['stock_price']}, volume {financial_data['volume']}."
                response = self.model.generate_content(prompt)
                financial_data["summary"] = response.text
            else:
                financial_data["summary"] = "Gemini Pro API not configured."

            return financial_data
        except Exception as e:
            print(f"Error fetching financial data for {self.company}: {str(e)}")
            return {}

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
    agent = FinancialAnalystAgent(company="Tesla")
    agent.run()