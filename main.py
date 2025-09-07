import os
from datetime import datetime
from agents.financial_analyst_agent import FinancialAnalystAgent

from agents.data_analyst_agent import DataAnalystAgent
from agents.research_agent import ResearchAgent
from agents.sentiment_analyst_agent import SentimentAnalystAgent
from agents.report_writer_agent import ReportWriterAgent
from agents.regulatory_analyst_agent import RegulatoryAnalystAgent
from agents.base_agent import BaseAgent


def validate_company(company: str) -> bool:
    """Check if company can be analyzed using yfinance."""
    agent = FinancialAnalystAgent(company)
    return agent.ticker_symbol is not None


def run_market_mind(company: str):
    """Run analysis for any global company."""
    print(f"\n=== MarketMind Analysis for {company} ===")
    
    # Validate API key first
    base = BaseAgent()
    if not base.validate_api_key():
        print("\n⚠️ Running with limited functionality (no AI analysis)")
        proceed = input("Continue anyway? (y/n): ").lower()
        if proceed != 'y':
            return

    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Initialize Financial Agent for ticker lookup
        financial_agent = FinancialAnalystAgent(company)
        if not financial_agent.ticker_symbol:
            print("\n❌ Company not found. Tips:")
            print("- Try the official company name")
            print("- Use local language name for Asian companies")
            print("- Add the exchange identifier (e.g., .NS for Indian NSE)")
            return False

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
    print("\nExample inputs:")
    print("🇺🇸 US: Apple, Microsoft, Tesla")
    print("🇮🇳 India: TCS.NS, Reliance.NS, HDFC.NS")
    print("🇯🇵 Japan: 7203.T (Toyota), 6758.T (Sony)")
    print("🇰🇷 Korea: 005930.KS (Samsung), 066570.KS (LG)")
    print("🇷🇺 Russia: GAZP.ME, SBER.ME")
    print("🇧🇷 Brazil: PETR4.SA, VALE3.SA")
    
    company = input("\nEnter company name or ticker: ").strip()
    run_market_mind(company)
