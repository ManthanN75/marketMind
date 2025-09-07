from dotenv import load_dotenv
import os
import google.generativeai as genai

class BaseAgent:
    def __init__(self):
        self.model = None
        self.setup_model()

    def setup_model(self):
        """Initialize Gemini model with proper error handling."""
        try:
            load_dotenv(override=True)

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in .env file")

            # Updated Gemini configuration
            genai.configure(api_key=api_key)

            # List available models first
            models = [m.name for m in genai.list_models()]
            print("Available models:", models)

            # Use the correct model name
            model_name = 'models/gemini-pro'
            if model_name not in models:
                raise ValueError(f"Model {model_name} not available. Please use one of: {models}")

            self.model = genai.GenerativeModel(model_name)
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

            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
            response = model.generate_content("Test")
            return True
        except Exception as e:
            print(f"❌ API key validation failed: {str(e)}")
            return False