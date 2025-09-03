import os
from datetime import datetime
from agents.financial_analyst_agent import FinancialAnalystAgent

from agents.data_analyst_agent import DataAnalystAgent
from agents.research_agent import ResearchAgent
from agents.sentiment_analyst_agent import SentimentAnalystAgent
from agents.report_writer_agent import ReportWriterAgent
from agents.regulatory_analyst_agent import RegulatoryAnalystAgent


def validate_company(company: str) -> bool:
    """Check if company can be analyzed using yfinance."""
    agent = FinancialAnalystAgent(company)
    return agent.ticker_symbol is not None


def run_market_mind(company: str):
    """Run all MarketMind agents in sequence."""
    print(f"\n=== MarketMind Analysis for {company} ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Validate company first
        financial_agent = FinancialAnalystAgent(company)
        if not financial_agent.ticker_symbol:
            print(f"❌ Error: Could not find valid ticker for {company}")
            print("Try using a simpler name (e.g., 'BMW' instead of 'Bayerische Motoren Werke AG')")
            return

        # Run agents
        print("🔍 Running Research Agent...")
        ResearchAgent(company=company).run()
        print("✅ Research Agent completed\n")

        # 2. Financial Analysis
        print("💹 Running Financial Analyst...")
        FinancialAnalystAgent(company=company).run()
        print("✅ Financial Analysis completed\n")

        # 3. Sentiment Analysis
        print("🎯 Running Sentiment Analyst...")
        SentimentAnalystAgent(company=company).run()
        print("✅ Sentiment Analysis completed\n")

        # 4. Data Analysis
        print("📊 Running Data Analyst...")
        DataAnalystAgent(company=company).run()
        print("✅ Data Analysis completed\n")

        # 5. Regulatory Analysis
        print("📋 Running Regulatory Analysis...")
        RegulatoryAnalystAgent(company=company).run()
        print("✅ Regulatory Analysis completed\n")

        # 6. Report Generation
        print("📝 Generating Final Report...")
        ReportWriterAgent(company=company).run()
        print("✅ Report Generation completed\n")

        print(f"Analysis completed successfully for {company}")
        print("Check the data folder for results")

    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("\nMarketMind - Global Company Analysis")
    print("Examples: BMW, Apple, Toyota")
    
    company = input("\nCompany name: ").strip()
    if not run_market_mind(company):
        print("\nTip: Try using the company's common name or stock symbol")
