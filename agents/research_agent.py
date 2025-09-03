"""
ResearchAgent: Scrapes news, press releases, and social media from global sources.
"""

import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime
import json
import os
from dotenv import load_dotenv

class ResearchAgent:
    def __init__(self, company, output_dir="data"):
        self.company = company
        self.output_dir = output_dir
        load_dotenv()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.setup_models()

    def setup_models(self):
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                print("Gemini model initialized successfully.")
            except Exception as e:
                print(f"Error initializing Gemini model: {str(e)}")
                self.model = None

    def scrape_news(self):
        """Scrape news from multiple sources."""
        news_data = []

        # Google News
        news_data.extend(self._scrape_google_news())

        # Company Press Releases
        news_data.extend(self._scrape_press_releases())

        return news_data

    def _scrape_google_news(self):
        try:
            url = f"https://news.google.com/rss/search?q={self.company}&hl=en-US&gl=US&ceid=US:en"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers, timeout=10)

            soup = BeautifulSoup(response.text, "xml")
            articles = []

            for item in soup.find_all("item")[:5]:
                title = item.title.text if item.title else None
                link = item.link.text if item.link else None
                pub_date = item.pubDate.text if item.pubDate else None

                if title and link:
                    articles.append({
                        "title": title,
                        "link": link,
                        "date": pub_date,
                        "source": "Google News"
                    })

            return articles
        except Exception as e:
            print(f"Error scraping Google News: {str(e)}")
            return []

    def _scrape_press_releases(self):
        try:
            # Add company-specific press release URLs
            press_urls = {
                "Samsung": "https://news.samsung.com/global/",
                "Tesla": "https://ir.tesla.com/press"
            }

            url = press_urls.get(self.company)
            if not url:
                return []

            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            articles = []
            # Customize selectors based on company website structure
            for item in soup.select("article, .press-release")[:3]:
                title = item.select_one("h2, h3, .title")
                link = item.select_one("a")

                if title and link:
                    articles.append({
                        "title": title.text.strip(),
                        "link": link["href"],
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "source": f"{self.company} Press Release"
                    })

            return articles
        except Exception as e:
            print(f"Error scraping press releases: {str(e)}")
            return []

    def run(self):
        """Execute the agent's tasks."""
        try:
            news_data = {
                "company": self.company,
                "news": self.scrape_news(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Create data directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Save to JSON file
            output_path = os.path.join(self.output_dir, "raw_data.json")
            with open(output_path, "w") as f:
                json.dump(news_data, f, indent=4)
            print(f"News data saved to {output_path}")
            
            return news_data
            
        except Exception as e:
            print(f"Error in Research Agent: {str(e)}")
            return {}