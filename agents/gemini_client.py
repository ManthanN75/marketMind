"""Shared Google Gen AI client setup for MarketMind agents."""

import os

from dotenv import load_dotenv
from google import genai


class GeminiModel:
    """Small compatibility wrapper for the project's text generation calls."""

    def __init__(self, api_key=None, model_name=None):
        load_dotenv()
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name or os.getenv(
            "GEMINI_MODEL", "gemini-3.8-flash"
        )

    def generate_content(self, prompt):
        """Generate a text response using the configured Gemini model."""
        return self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )


def create_gemini_model(api_key=None):
    """Create the shared model wrapper used by each analysis agent."""
    return GeminiModel(api_key=api_key)
