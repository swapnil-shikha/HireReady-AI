import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SPEECHMATICS_API_KEY = os.getenv("SPEECHMATICS_API_KEY")

BASE_URL = "https://asr.api.speechmatics.com/v2"

# Voice options (can be expanded)
AI_VOICES = {
    "male": {"name": "Alex", "code": "en-US"},
    "female": {"name": "Emma", "code": "en-US"},
}

def get_ai_voice_details():
    """Return available AI voices with name + code"""
    return AI_VOICES

def speak_text(text, voice="en-US"):
    """
    Convert text to speech using Speechmatics API and play in Streamlit.
    """
    if not SPEECHMATICS_API_KEY:
        st.error("Speechmatics API key not found. Please set SPEECHMATICS_API_KEY in .env")
        return

    try:
        url = f"{BASE_URL}/tts"
        headers = {"Authorization": f"Bearer {SPEECHMATICS_API_KEY}"}
        payload = {
            "text": text,
            "voice": voice,
            "format": "mp3"
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            st.error(f"TTS Error: {response.status_code} - {response.text}")
            return

        audio_bytes = response.content
        st.audio(audio_bytes, format="audio/mp3")

    except Exception as e:
        st.error(f"Speech synthesis failed: {e}")
