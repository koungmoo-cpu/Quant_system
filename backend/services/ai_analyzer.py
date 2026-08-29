import json
from google import genai
from google.genai import types
import sys
import os

# To import from config when running as a module or in FastAPI
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import settings
except ImportError:
    class MockSettings:
        google_genai_api_key = "mock"
    settings = MockSettings()

class AIAnalyzer:
    def __init__(self):
        # Initialize the GenAI client with API key from settings
        api_key = settings.google_genai_api_key
        # For safety if api key is not set yet in .env
        if not api_key:
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
            
        self.model_name = "gemini-3.6-flash"

    def analyze(self, ticker: str, strategy_name: str, context: dict, price_data_summary: str) -> dict:
        """
        Sends the filtered setup to Gemini API for qualitative analysis.
        Returns a dictionary with 'action' (BUY, WAIT, SELL) and 'summary' (3 lines).
        """
        if not self.client:
            return {
                "action": "WAIT",
                "summary": "API Key not configured.\nPlease set GOOGLE_GENAI_API_KEY.\nCannot perform AI analysis."
            }

        prompt = f"""
You are a top-tier Wall Street quantitative analyst and trading expert.
Analyze the following stock setup which has passed our technical filters.

Ticker: {ticker}
Strategy Matched: {strategy_name}
Context: {json.dumps(context)}
Price Data Summary: {price_data_summary}

Task:
1. Evaluate if this is a high-probability trade based on the principles of {strategy_name}.
2. Provide exactly one ACTION TAG: BUY, WAIT, or SELL.
3. Provide a strict 3-line summary explaining the fundamental/technical reasoning.

You must return valid JSON in the exact following format:
{{
    "action": "BUY",
    "summary": "Line 1 reasoning.\\nLine 2 reasoning.\\nLine 3 reasoning."
}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            
            result = json.loads(response.text)
            action = result.get("action", "WAIT").upper()
            if action not in ["BUY", "WAIT", "SELL"]:
                action = "WAIT"
                
            return {
                "action": action,
                "summary": result.get("summary", "Analysis completed without detailed summary.")
            }
        except Exception as e:
            print(f"Error calling Gemini API for {ticker}: {e}")
            return {
                "action": "WAIT",
                "summary": f"Error during AI analysis.\\nException:\\n{str(e)}"
            }
