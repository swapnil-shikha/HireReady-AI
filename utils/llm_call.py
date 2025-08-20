from litellm import completion, RateLimitError
import os
import json
import time

# Load API key and model from environment variables
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral/mistral-large-latest")

# Retry configuration
MAX_RETRIES = 5
RETRY_DELAY = 10  # seconds

def get_response_from_llm(prompt):
    """
    Calls the LLM and returns the response.
    Retries automatically if rate limit is hit.

    Args:
        prompt (str): The string to prompt the LLM with.

    Returns:
        str: The response from the LLM.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = completion(
                model=LLM_MODEL,
                api_key=MISTRAL_API_KEY,
                messages=[{"role": "user", "content": prompt}],
            )
            # Return the actual message content
            return response.choices[0].message.content
        except RateLimitError:
            if attempt < MAX_RETRIES:
                print(f"Rate limit hit. Retrying in {RETRY_DELAY} seconds... (Attempt {attempt}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(
                    "Mistral API rate limit exceeded after multiple retries. "
                    "Please try again later or upgrade your plan."
                )

def parse_json_response(response):
    """
    Safely parse JSON response from LLM.

    Args:
        response (str): The raw LLM response.

    Returns:
        dict or None: Parsed JSON, or None if parsing fails.
    """
    try:
        # Remove code fences if present
        cleaned = response.strip().lstrip("```json").rstrip("```")
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None
