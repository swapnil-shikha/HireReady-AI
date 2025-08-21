# utils/transcript_audio.py

import requests
import os
from dotenv import load_dotenv
load_dotenv()

SPEECHMATICS_API_KEY = os.getenv("SPEECHMATICS_API_KEY")
BASE_URL = "https://asr.api.speechmatics.com/v2"

def transcribe_with_speechmatics(audio_file_path: str) -> str:
    """
    Send audio file to Speechmatics ASR and return the transcript.
    """
    if not SPEECHMATICS_API_KEY:
        raise ValueError("SPEECHMATICS_API_KEY not set in .env")

    headers = {"Authorization": f"Bearer {SPEECHMATICS_API_KEY}"}
    files = {"audio": open(audio_file_path, "rb")}

    try:
        response = requests.post(f"{BASE_URL}/transcribe", headers=headers, files=files)
        response.raise_for_status()
        data = response.json()
        # The actual key may differ depending on Speechmatics API response
        transcript = data.get("results", {}).get("transcript", "")
        return transcript
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return ""
