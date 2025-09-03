import json
import os
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

class RegulatoryAnalystAgent:
    def __init__(self, company, input_dir="data", output_dir="data"):
        self.company = company
        self.input_dir = input_dir
        self.output_dir = output_dir
        self._load_regulatory_map()
        load_dotenv()
        self.setup_model()

    def _load_regulatory_map(self):
        """Load company-specific regulatory focus areas."""
        self.regulatory_map = {
            "Samsung": {
                "regions": ["South Korea", "EU", "US"],
                "keywords": ["GDPR", "antitrust", "FTC", "privacy", "consumer protection"]
            },
            "Tesla": {
                "regions": ["US", "EU", "China"],
                "keywords": ["emissions", "safety", "autonomous", "NHTSA", "recall"]
            }
            # Add other companies as needed
        }

    def setup_model(self):
        """Initialize Gemini for regulatory analysis."""
        if api_key := os.getenv("GEMINI_API_KEY"):
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
            print("Warning: Gemini API key not found")

    def analyze_regulations(self):
        """Analyze regulatory mentions in news data."""
        try:
            # Load news data
            with open(os.path.join(self.input_dir, "raw_data.json"), "r") as f:
                news_data = json.load(f)

            company_regs = self.regulatory_map.get(self.company, {})
            regulatory_findings = {
                "company": self.company,
                "timestamp": datetime.now().isoformat(),
                "regulatory_mentions": [],
                "compliance_risks": [],
                "summary": ""
            }

            # Analyze news articles for regulatory mentions
            for article in news_data.get("news", []):
                title = article.get("title", "").lower()
                
                # Check for regulatory keywords
                for keyword in company_regs.get("keywords", []):
                    if keyword.lower() in title:
                        regulatory_findings["regulatory_mentions"].append({
                            "regulation": keyword,
                            "title": article["title"],
                            "link": article["link"]
                        })

            # Generate analysis using Gemini
            if self.model and regulatory_findings["regulatory_mentions"]:
                analysis = self._generate_analysis(regulatory_findings["regulatory_mentions"])
                regulatory_findings["summary"] = analysis

            return regulatory_findings

        except Exception as e:
            print(f"Error in regulatory analysis: {str(e)}")
            return {}

    def _generate_analysis(self, mentions):
        """Generate regulatory impact analysis."""
        try:
            prompt = f"""Analyze these regulatory mentions for {self.company}:
            {json.dumps(mentions, indent=2)}
            
            Provide a brief summary of regulatory implications and compliance risks."""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating analysis: {str(e)}")
            return "Analysis generation failed"

    def save_data(self, regulatory_data):
        """Save regulatory analysis to JSON."""
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "regulatory_data.json")
        
        try:
            with open(output_path, "w") as f:
                json.dump(regulatory_data, f, indent=4)
            print(f"Regulatory data saved to {output_path}")
        except Exception as e:
            print(f"Error saving regulatory data: {str(e)}")

    def run(self):
        """Execute the agent's tasks."""
        regulatory_data = self.analyze_regulations()
        if regulatory_data:
            self.save_data(regulatory_data)
        return regulatory_data

if __name__ == "__main__":
    agent = RegulatoryAnalystAgent(company="Samsung")
    agent.run()