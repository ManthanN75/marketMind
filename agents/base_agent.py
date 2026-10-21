from dotenv import load_dotenv
import os
from agents.gemini_client import create_gemini_model

class BaseAgent:
    def __init__(self):
        self.model = None
        self.setup_model()

    def setup_model(self):
        """Initialize model with proper error handling."""
        try:
            load_dotenv(override=True)

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in .env file")

            self.model = create_gemini_model(api_key)
            print("✅ Gemini API connected successfully")
            return True

        except Exception as e:
            print(f"❌ Gemini API setup failed: {str(e)}")
            self.model = None
            return False

    def validate_api_key(self):
        """Validate Gemini API key."""
        try:
            if not os.getenv("GEMINI_API_KEY"):
                print("❌ Warning: GEMINI_API_KEY not found")
                return False

            model = create_gemini_model(os.getenv("GEMINI_API_KEY"))
            response = model.generate_content("Reply with the word OK.")
            return bool(response.text)
        except Exception as e:
            print(f"❌ API key validation failed: {str(e)}")
            return False
