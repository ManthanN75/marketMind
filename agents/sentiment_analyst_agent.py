import json
import os
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from textblob import TextBlob
import nltk
import re

class SentimentAnalystAgent:
    def __init__(self, company, input_dir="data", output_dir="data"):
        # Ensure NLTK data is downloaded
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            print("Downloading required NLTK data...")
            nltk.download('punkt')
            nltk.download('averaged_perceptron_tagger')
        
        self.company = company
        self.input_dir = input_dir
        self.output_dir = output_dir
        load_dotenv()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                # Updated model name to the correct one
                self.model = genai.GenerativeModel('gemini-pro')
                print("Gemini model initialized successfully.")
            except Exception as e:
                print(f"Error initializing Gemini model: {str(e)}")
                self.model = None

        # Add Twitter/X API configuration
        self.twitter_api_key = os.getenv("TWITTER_API_KEY")
        self.twitter_api_secret = os.getenv("TWITTER_API_SECRET")

    def detect_lawsuits(self, text):
        """Detect potential legal issues in text."""
        lawsuit_keywords = [
            'lawsuit', 'sued', 'legal action', 'court', 'litigation',
            'settlement', 'class action', 'dispute', 'patent', 'infringement'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in lawsuit_keywords)

    def get_social_sentiment(self):
        """Get sentiment from X (Twitter) posts."""
        if not (self.twitter_api_key and self.twitter_api_secret):
            return []
            
        try:
            import tweepy
            
            auth = tweepy.OAuthHandler(self.twitter_api_key, self.twitter_api_secret)
            api = tweepy.API(auth)
            
            # Search recent tweets about the company
            query = f"{self.company} -filter:retweets"
            tweets = api.search_tweets(q=query, lang="en", count=100)
            
            social_data = []
            for tweet in tweets:
                blob = TextBlob(tweet.text)
                social_data.append({
                    "text": tweet.text,
                    "sentiment_score": round(blob.sentiment.polarity, 3),
                    "subjectivity": round(blob.sentiment.subjectivity, 3),
                    "followers": tweet.user.followers_count,
                    "timestamp": tweet.created_at.isoformat(),
                    "has_legal_concern": self.detect_lawsuits(tweet.text)
                })
            
            return social_data
        except Exception as e:
            print(f"Error fetching social sentiment: {str(e)}")
            return []

    def analyze_sentiment(self):
        try:
            # Get news sentiment
            news_sentiment = self._analyze_news_sentiment()
            
            # Get social media sentiment
            social_sentiment = self.get_social_sentiment()
            
            # Combine both sources
            sentiment_data = {
                "company": self.company,
                "sentiment_analysis": {
                    "news_sentiment": news_sentiment,
                    "social_sentiment": social_sentiment,
                    "combined_score": 0.0,
                    "articles_analyzed": len(news_sentiment["articles"]),
                    "social_posts_analyzed": len(social_sentiment),
                    "summary": ""
                },
                "legal_concerns": [],
                "potential_risks": [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Enhanced legal analysis using Gemini
            if self.model:
                legal_prompt = f"""Analyze these headlines for legal issues:
                {' | '.join([a['title'] for a in news_sentiment['articles']])}
                
                Identify:
                1. Potential lawsuits
                2. Regulatory concerns
                3. Patent disputes
                4. Class action possibilities
                5. International legal implications
                
                Format as JSON with categories and confidence scores.
                """
                
                try:
                    legal_analysis = self.model.generate_content(legal_prompt)
                    sentiment_data["legal_analysis"] = legal_analysis.text
                except Exception as e:
                    print(f"Error in legal analysis: {str(e)}")
            
            return sentiment_data
        
        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            return {}

    def _analyze_news_sentiment(self):
        """Analyze sentiment from news articles."""
        try:
            input_path = os.path.join(self.input_dir, "raw_data.json")
            with open(input_path, "r") as f:
                news_data = json.load(f)

            sentiment_result = {
                "articles": [],
                "overall_score": 0.0,
                "legal_concerns": []
            }

            texts = [article["title"] for article in news_data.get("news", [])]
            
            if not texts:
                return sentiment_result

            total_sentiment = 0
            for article in news_data.get("news", []):
                title = article["title"]
                blob = TextBlob(title)
                
                # Enhanced sentiment scoring
                base_score = blob.sentiment.polarity
                
                # Context-based adjustments
                positive_indicators = ['launch', 'innovation', 'growth', 'partnership', 'success']
                negative_indicators = ['lawsuit', 'dispute', 'decline', 'investigation', 'concern']
                
                for word in positive_indicators:
                    if word in title.lower():
                        base_score += 0.1
                for word in negative_indicators:
                    if word in title.lower():
                        base_score -= 0.1
                
                # Normalize score
                final_score = max(min(base_score, 1.0), -1.0)
                
                # Legal analysis
                legal_concerns = self.detect_lawsuits(title)
                if legal_concerns:
                    sentiment_result["legal_concerns"].append({
                        "title": title,
                        "link": article["link"],
                        "concern_type": "potential_lawsuit",
                        "severity": "high" if base_score < -0.3 else "medium"
                    })

                article_data = {
                    "title": title,
                    "sentiment_score": round(final_score, 3),
                    "subjectivity": round(blob.sentiment.subjectivity, 3),
                    "link": article["link"],
                    "keywords": [word for word, tag in blob.tags if tag.startswith('NN')],
                    "has_legal_concern": bool(legal_concerns),
                    "timestamp": datetime.now().isoformat()
                }
                
                sentiment_result["articles"].append(article_data)
                total_sentiment += final_score

            sentiment_result["overall_score"] = round(total_sentiment / len(texts), 3)
            return sentiment_result

        except Exception as e:
            print(f"Error in news sentiment analysis: {str(e)}")
            return {"articles": [], "overall_score": 0.0, "legal_concerns": []}

    def save_data(self, sentiment_data):
        """Save sentiment data to JSON file."""
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "sentiment_data.json")
        try:
            with open(output_path, "w") as f:
                json.dump(sentiment_data, f, indent=4)
            print(f"Sentiment data saved to {output_path}")
        except Exception as e:
            print(f"Error saving sentiment data: {str(e)}")

    def run(self):
        """Execute the agent's tasks."""
        sentiment_data = self.analyze_sentiment()
        if sentiment_data:
            self.save_data(sentiment_data)
        return sentiment_data

if __name__ == "__main__":
    agent = SentimentAnalystAgent(company="Samsung")
    agent.run()