import json
import os
from datetime import datetime
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import google.generativeai as genai

class DataAnalystAgent:
    def __init__(self, company, input_dir="data", output_dir="data"):
        self.company = company
        self.input_dir = input_dir
        self.output_dir = output_dir
        self._load_competitor_map()
        load_dotenv()
        self.setup_models()
    
    def _load_competitor_map(self):
        """Load company-competitor mapping."""
        self.competitor_map = {
            "Samsung": ["Apple", "LG", "Sony", "Xiaomi"],
            "Tesla": ["Ford", "GM", "Volkswagen", "BYD"],
            "Toyota": ["Honda", "Volkswagen", "Hyundai", "Ford"],
            "Volkswagen": ["Toyota", "BMW", "Mercedes", "Tesla"]
        }

    def setup_models(self):
        """Initialize Gemini model for advanced analysis."""
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                print("Gemini model initialized successfully.")
            except Exception as e:
                print(f"Error initializing Gemini model: {str(e)}")
                self.model = None

    def analyze_data(self):
        """Process and analyze all available data."""
        try:
            # Load data from various sources
            financial_data = self._load_json("financial_data.json")
            news_data = self._load_json("raw_data.json")
            sentiment_data = self._load_json("sentiment_data.json")

            analysis_results = {
                "company": self.company,
                "timestamp": datetime.now().isoformat(),
                "market_trends": self._analyze_market_trends(financial_data),
                "competitor_analysis": self._analyze_competitors(news_data),
                "opportunities": self._identify_opportunities(financial_data, sentiment_data),
                "risk_factors": self._analyze_risks(financial_data, sentiment_data),
                "summary": ""
            }

            # Generate summary using Gemini
            if self.model:
                analysis_results["summary"] = self._generate_summary(analysis_results)

            return analysis_results

        except Exception as e:
            print(f"Error in data analysis: {str(e)}")
            return {}

    def _load_json(self, filename):
        """Load JSON data from file."""
        try:
            with open(os.path.join(self.input_dir, filename), 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {str(e)}")
            return {}

    def _analyze_market_trends(self, financial_data):
        """Analyze market trends from financial data."""
        trends = []
        try:
            price_change = financial_data.get("price_change_percent", 0)
            market_cap = financial_data.get("market_cap_formatted", "N/A")
            
            # Price trend analysis
            if abs(price_change) > 5:
                trends.append({
                    "type": "price_movement",
                    "description": f"Significant price movement of {price_change}%",
                    "impact": "high" if abs(price_change) > 10 else "medium"
                })

            # Market position analysis
            if market_cap != "N/A":
                trends.append({
                    "type": "market_position",
                    "description": f"Market cap: {market_cap}",
                    "impact": "stable" if price_change > -5 else "concerning"
                })

            return trends
        except Exception as e:
            print(f"Error analyzing market trends: {str(e)}")
            return []

    def _analyze_competitors(self, news_data):
        """Analyze competitor mentions and activities."""
        competitors = self.competitor_map.get(self.company, [])
        competitor_analysis = []

        try:
            for competitor in competitors:
                mentions = sum(1 for article in news_data.get("news", [])
                             if competitor.lower() in article["title"].lower())
                
                if mentions > 0:
                    competitor_analysis.append({
                        "competitor": competitor,
                        "mentions": mentions,
                        "relevance": "high" if mentions > 2 else "medium"
                    })

        except Exception as e:
            print(f"Error analyzing competitors: {str(e)}")

        return competitor_analysis

    def _identify_opportunities(self, financial_data, sentiment_data):
        """Identify business opportunities."""
        opportunities = []
        try:
            # Financial opportunities
            if financial_data.get("price_change_percent", 0) < 0:
                opportunities.append({
                    "type": "investment",
                    "description": "Potential buying opportunity",
                    "confidence": "medium"
                })

            # Sentiment-based opportunities
            if sentiment_data.get("sentiment_analysis", {}).get("overall_score", 0) > 0.2:
                opportunities.append({
                    "type": "market_sentiment",
                    "description": "Positive market sentiment indicates growth potential",
                    "confidence": "high"
                })

        except Exception as e:
            print(f"Error identifying opportunities: {str(e)}")

        return opportunities

    def _analyze_risks(self, financial_data, sentiment_data):
        """Analyze potential risks."""
        risks = []
        try:
            # Financial risks
            if financial_data.get("price_change_percent", 0) < -5:
                risks.append({
                    "type": "market_risk",
                    "description": "Significant price decline",
                    "severity": "high"
                })

            # Sentiment risks
            if sentiment_data.get("legal_concerns"):
                risks.append({
                    "type": "legal_risk",
                    "description": "Active legal concerns detected",
                    "severity": "high"
                })

        except Exception as e:
            print(f"Error analyzing risks: {str(e)}")

        return risks

    def _generate_summary(self, analysis):
        """Generate summary using Gemini."""
        try:
            prompt = f"""Analyze this market data for {self.company}:
            Market Trends: {analysis['market_trends']}
            Competitor Analysis: {analysis['competitor_analysis']}
            Opportunities: {analysis['opportunities']}
            Risks: {analysis['risk_factors']}

            Provide a concise summary of the key findings and strategic implications.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return "Summary generation failed"

    def save_data(self, analysis_data):
        """Save analysis results to JSON."""
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "analysis_data.json")
        
        try:
            with open(output_path, "w") as f:
                json.dump(analysis_data, f, indent=4)
            print(f"Analysis data saved to {output_path}")
        except Exception as e:
            print(f"Error saving analysis data: {str(e)}")

    def run(self):
        """Execute the agent's tasks."""
        analysis_data = self.analyze_data()
        if analysis_data:
            self.save_data(analysis_data)
        return analysis_data

if __name__ == "__main__":
    agent = DataAnalystAgent(company="Samsung")
    agent.run()