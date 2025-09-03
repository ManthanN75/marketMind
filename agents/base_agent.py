import google.generativeai as genai
from dotenv import load_dotenv
import os

class BaseAgent:
    def setup_model(self):
        """Initialize Gemini model with correct configuration."""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("Warning: GEMINI_API_KEY not found in .env")
                return None
                
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            return self.model
        except Exception as e:
            print(f"Error initializing Gemini model: {str(e)}")
            return None