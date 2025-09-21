"""
ResearchAgent: Enhanced version with multiple news sources and better error handling.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
import time
import random


class ResearchAgent:
    def __init__(self, company, output_dir="data"):
        self.company = company
        self.output_dir = output_dir
        load_dotenv()
        self.setup_models()
        self.session = requests.Session()
        self.setup_session()

    def setup_session(self):
        """Setup requests session with proper headers and retry logic."""
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

    def setup_models(self):
        """Initialize Gemini model."""
        if api_key := os.getenv("GEMINI_API_KEY"):
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
            print("Gemini model initialized successfully.")
        else:
            self.model = None
            print("Warning: GEMINI_API_KEY not found")

    def scrape_google_news(self):
        """Scrape Google News RSS with better error handling."""
        articles = []
        try:
            encoded_company = requests.utils.quote(self.company)
            url = f"https://news.google.com/rss/search?q={encoded_company}&hl=en-US&gl=US&ceid=US:en"
            
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "xml")

                for item in soup.find_all("item")[:10]:  # Get more articles
                    try:
                        title = item.title.text if item.title else "No title"
                        link = item.link.text if item.link else ""
                        pub_date = item.pubDate.text if item.pubDate else ""

                        # Extract description if available
                        description = ""
                        if item.description:
                            desc_soup = BeautifulSoup(item.description.text, 'html.parser')
                            description = desc_soup.get_text()[:200]  # First 200 chars

                        articles.append({
                            "title": title,
                            "link": link,
                            "date": pub_date,
                            "description": description,
                            "source": "Google News"
                        })
                    except Exception as e:
                        print(f"Error parsing article: {str(e)}")
                        continue

            else:
                print(f"Google News returned status code: {response.status_code}")

        except Exception as e:
            print(f"Error fetching Google News: {str(e)}")

        return articles

    def scrape_yahoo_finance_news(self):
        """Scrape Yahoo Finance news."""
        articles = []
        try:
            # Yahoo Finance search URL
            encoded_company = requests.utils.quote(self.company)
            url = f"https://finance.yahoo.com/quote/{encoded_company}/news"

            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))

            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Look for news articles (Yahoo Finance specific selectors)
                news_items = soup.find_all(['h3', 'div'], class_=lambda x: x and ('StreamItemTitle' in x or 'story-title' in x))

                for item in news_items[:5]:
                    try:
                        title_elem = item.find('a') or item
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            link = title_elem.get('href', '')
                            if link and not link.startswith('http'):
                                link = f"https://finance.yahoo.com{link}"

                            if title and len(title) > 10:  # Filter out short/empty titles
                                articles.append({
                                    "title": title,
                                    "link": link,
                                    "date": datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'),
                                    "description": "",
                                    "source": "Yahoo Finance"
                                })
                    except Exception as e:
                        print(f"Error parsing Yahoo Finance article: {str(e)}")
                        continue

        except Exception as e:
            print(f"Error fetching Yahoo Finance news: {str(e)}")

        return articles

    def scrape_marketwatch_news(self):
        """Scrape MarketWatch news."""
        articles = []
        try:
            encoded_company = requests.utils.quote(self.company)
            url = f"https://www.marketwatch.com/tools/quotes/lookup.asp?siteID=mktw&Lookup={encoded_company}"

            time.sleep(random.uniform(1, 2))

            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # MarketWatch news selectors
                news_items = soup.find_all('h3', class_=lambda x: x and 'headline' in x.lower())

                for item in news_items[:3]:
                    try:
                        title_elem = item.find('a')
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            link = title_elem.get('href', '')
                            if link and not link.startswith('http'):
                                link = f"https://www.marketwatch.com{link}"

                            articles.append({
                                "title": title,
                                "link": link,
                                "date": datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'),
                                "description": "",
                                "source": "MarketWatch"
                            })
                    except Exception as e:
                        print(f"Error parsing MarketWatch article: {str(e)}")
                        continue

        except Exception as e:
            print(f"Error fetching MarketWatch news: {str(e)}")

        return articles

    def scrape_news(self):
        """Scrape news from multiple sources."""
        all_articles = []

        # Try multiple sources
        sources = [
            ("Google News", self.scrape_google_news),
            ("Yahoo Finance", self.scrape_yahoo_finance_news),
            ("MarketWatch", self.scrape_marketwatch_news)
        ]

        for source_name, scraper_func in sources:
            try:
                print(f"Fetching from {source_name}...")
                articles = scraper_func()
                all_articles.extend(articles)

                if articles:
                    print(f"Found {len(articles)} articles from {source_name}")
                else:
                    print(f"No articles found from {source_name}")

            except Exception as e:
                print(f"Error with {source_name}: {str(e)}")
                continue

        # Remove duplicates based on title
        seen_titles = set()
        unique_articles = []

        for article in all_articles:
            title_lower = article['title'].lower()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_articles.append(article)

        print(f"Total unique articles found: {len(unique_articles)}")
        return unique_articles

    def analyze_news_relevance(self, articles):
        """Use Gemini to analyze news relevance and extract key insights."""
        if not self.model or not articles:
            return articles

        try:
            # Create a summary of all headlines for analysis
            headlines = [article['title'] for article in articles[:10]]
            headlines_text = '\n'.join([f"{i+1}. {title}" for i, title in enumerate(headlines)])

            prompt = f"""Analyze these news headlines about {self.company}:

{headlines_text}

For each headline, provide:
1. Relevance score (1-10)
2. Sentiment (positive/negative/neutral)
3. Key topics (e.g., financial, legal, product, market)
4. Priority level (high/medium/low)

Format as JSON array with objects containing: headline_number, relevance_score, sentiment, topics, priority
"""

            response = self.model.generate_content(prompt)
            analysis_text = response.text.strip()

            # Try to extract JSON from the response
            try:
                # Look for JSON-like content in the response
                start = analysis_text.find('[')
                end = analysis_text.rfind(']') + 1
                if start >= 0 and end > start:
                    analysis_json = json.loads(analysis_text[start:end])

                    # Add analysis data to articles
                    for i, analysis in enumerate(analysis_json):
                        if i < len(articles):
                            articles[i]['ai_analysis'] = analysis

            except json.JSONDecodeError:
                print("Could not parse AI analysis as JSON")

        except Exception as e:
            print(f"Error in AI analysis: {str(e)}")

        return articles

    def save_data(self, news_data):
        """Save news data to JSON file."""
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "raw_data.json")

        try:
            with open(output_path, "w", encoding='utf-8') as f:
                json.dump(news_data, f, indent=4, ensure_ascii=False)
            print(f"News data saved to {output_path}")
        except Exception as e:
            print(f"Error saving news data: {str(e)}")

    def run(self):
        """Execute the agent's tasks."""
        try:
            print(f"Starting news research for: {self.company}")

            # Scrape news from multiple sources
            articles = self.scrape_news()

            if not articles:
                print("No articles found. Creating minimal data structure.")
                articles = [{
                    "title": f"No recent news found for {self.company}",
                    "link": "",
                    "date": datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'),
                    "description": "No news articles were retrieved from available sources.",
                    "source": "System"
                }]

            # Analyze relevance using AI if available
            if self.model and len(articles) > 1:
                articles = self.analyze_news_relevance(articles)

            news_data = {
                "company": self.company,
                "news": articles,
                "total_articles": len(articles),
                "sources_used": list(set(article.get('source', 'Unknown') for article in articles)),
                "timestamp": datetime.now().isoformat(),
                "search_query": self.company
            }

            self.save_data(news_data)
            print(f"Research completed. Found {len(articles)} articles.")
            
            return news_data

        except Exception as e:
            print(f"Error in Research Agent: {str(e)}")
            return {
                "company": self.company,
                "news": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


if __name__ == "__main__":
    agent = ResearchAgent(company="Samsung")
    result = agent.run()
    print(json.dumps(result, indent=2))