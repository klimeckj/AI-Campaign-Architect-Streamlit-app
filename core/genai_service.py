"""Google Gemini AI service for content generation."""
import time
import streamlit as st
from google import genai


class GeminiClient:
    """Wrapper for Google Gemini API interactions."""
    
    def __init__(self, api_key, model_id="gemma-3-1b-it"):
        """Initialize Gemini client."""
        self.api_key = api_key
        self.model_id = model_id
        self.client = None
        if api_key:
            try:
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"Failed to initialize Gemini client: {e}")
    
    def is_connected(self):
        """Check if client is properly initialized."""
        return self.client is not None
    
    def generate_content(self, prompt, temperature=0.7):
        """Generate content using Gemini API."""
        if not self.client:
            raise Exception("API Key not found")
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={"temperature": temperature}
            )
            
            # Try different ways to extract text
            text_content = None
            
            # Method 1: Direct text attribute
            if hasattr(response, 'text'):
                text_content = response.text
            
            # Method 2: Check candidates
            if not text_content and hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content'):
                        if hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text'):
                                    text_content = part.text
                                    break
            
            # Fallback
            if not text_content:
                text_content = str(response)
            
            return text_content
            
        except Exception as e:
            raise Exception(f"Gemini Error: {str(e)}")


def generate_content_safe(client, prompt):
    """Safely generate content with error handling."""
    if not client or not client.is_connected():
        raise Exception("API Key not found - client not initialized")
    return client.generate_content(prompt)


def refine_content(client, unused_template, full_prompt):
    """
    Refinement pattern: Evolve existing content based on feedback.
    
    Args:
        client: GeminiClient instance
        unused_template: (unused - kept for compatibility)
        full_prompt: Complete prompt with all placeholders already filled
    
    Returns:
        str: Refined content
    """
    if not client or not client.is_connected():
        raise Exception("API Key not found - client not initialized")
    
    # Call Gemini with slightly lower temperature for more focused refinement
    return client.generate_content(full_prompt, temperature=0.5)


def extract_json_from_response(response_text):
    """
    Extract JSON from LLM response, handling various formats.
    
    Args:
        response_text: Raw response from LLM
    
    Returns:
        dict: Parsed JSON object
    """
    import json
    import re
    
    # Remove markdown code block markers
    clean = response_text.replace("```json", "").replace("```", "").strip()
    
    # Try direct JSON parse first
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON object in the text using regex
    json_match = re.search(r'\{.*\}', clean, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # If all else fails, raise detailed error
    raise ValueError(f"Nelze parsovat JSON z odpovědi. Text: {response_text[:200]}")


def mock_strategy_response(product, target):
    """Generate mock strategy response for offline mode."""
    time.sleep(1)
    return f"**[OFFLINE MODE]** Strategie pro {product} ({target}). API neodpovídá."


def mock_copy_generation(product):
    """Generate mock copy for offline mode."""
    time.sleep(1)
    return {
        "email_subject": f"[OFFLINE] {product}",
        "email_body": "Text se nepodařilo vygenerovat.",
        "sms_text": "Chyba API.",
        "push_text": "Chyba API."
    }
