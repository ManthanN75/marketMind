"""
ResearchAgent: Scrapes news, press releases, and social media from global sources.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

class ResearchAgent:
    def __init__(self, company, output_dir="data"):
        self.company = company
        self.output_dir = output_dir
        load_dotenv()
        self.setup_models()

    def setup_models(self):
        """Initialize Gemini model."""
        if api_key := os.getenv("GEMINI_API_KEY"):
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
            print("Gemini model initialized successfully.")
        else:
            self.model = None
            print("Warning: GEMINI_API_KEY not found")

    def scrape_news(self):
        """Scrape news from multiple sources."""
        try:
            articles = []
            
            # Try Google News RSS
            encoded_company = requests.utils.quote(self.company)
            url = f"https://news.google.com/rss/search?q={encoded_company}&hl=en-US&gl=US&ceid=US:en"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
                "Accept": "application/xml,application/xhtml+xml,text/html",
                "Accept-Language": "en-US,en;q=0.9",
            }

            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "xml")
                    for item in soup.find_all("item")[:5]:
                        articles.append({
                            "title": item.title.text if item.title else None,
                            "link": item.link.text if item.link else None,
                            "date": item.pubDate.text if item.pubDate else None,
                            "source": "Google News"
                        })
            except requests.RequestException as e:
                print(f"Warning: Could not fetch Google News - {str(e)}")

            # If no articles found, try alternative source
            if not articles:
                alternative_url = f"https://api.marketaux.com/v1/news/all?symbols={encoded_company}&api_token={os.getenv('MARKETAUX_API_KEY')}"
                try:
                    response = requests.get(alternative_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        for item in data.get('data', [])[:5]:
                            articles.append({
                                "title": item.get('title'),
                                "link": item.get('url'),
                                "date": item.get('published_at'),
                                "source": item.get('source')
                            })
                except:
                    pass

            return articles

        except Exception as e:
            print(f"Error in news scraping: {str(e)}")
            return []

    def run(self):
        """Execute the agent's tasks."""
        try:
            news_data = {
                "company": self.company,
                "news": self.scrape_news(),
                "timestamp": datetime.now().isoformat()
            }

            os.makedirs(self.output_dir, exist_ok=True)
            output_path = os.path.join(self.output_dir, "raw_data.json")

            with open(output_path, "w") as f:
                json.dump(news_data, f, indent=4)
            print(f"News data saved to {output_path}")
            
            return news_data

        except Exception as e:
            print(f"Error in Research Agent: {str(e)}")
            return {}