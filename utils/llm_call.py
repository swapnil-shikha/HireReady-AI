from litellm import completion
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

LLM_MODEL = os.environ.get("LLM_MODEL", "mistral/mistral-large-latest")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")


def get_response_from_llm(prompt):
    """
    Calls the LLM and returns the response.
    """
    if not MISTRAL_API_KEY:
        raise ValueError("❌ MISTRAL_API_KEY is not set. Please check your .env file.")

    response = completion(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        api_key=MISTRAL_API_KEY,  # use API key safely
    )
    return response.choices[0].message.content


def parse_json_response(response):
    # Parse the JSON response
    try:
        response = response.strip("```json").strip("```")
        return json.loads(response)
    except json.JSONDecodeError:
        return None
