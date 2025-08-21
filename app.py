
import os
import certifi

from dotenv import load_dotenv
os.environ["SSL_CERT_FILE"] = certifi.where()
load_dotenv()


import asyncio
from datetime import datetime
import json

import streamlit as st

# ---- Corrected Imports based on your project's file structure ----
from utils.transcript_audio import transcribe_with_speechmatics
# The correct import for resume extraction must be from a different file
from utils.basic_details import get_ai_greeting_message, get_final_thanks_message, extract_resume_info_using_llm
from utils.text_to_speech import speak_text
from utils.analyze_candidate import analyze_candidate_response_and_generate_new_question

from utils.evaluation import get_feedback_of_candidate_response, get_overall_evaluation_score
from utils.save_interview_data import save_interview_data
from utils.load_content import load_content_streamlit

# --------------------
# App Constants
# --------------------
MAX_QUESTIONS = 5

VOICE_CARDS = {
    "Zephyr (Bright)": {"icon": "🎙️", "tag": "US • Bright", "code": "en-US-ZephyrNeural"},
    "Puck (Upbeat)": {"icon": "🎶", "tag": "US • Upbeat", "code": "en-US-PuckNeural"},
    "Callirrhoe (Easy-going)": {"icon": "🤙", "tag": "US • Casual", "code": "en-US-CallirrhoeNeural"},
    "Algieba (Smooth)": {"icon": "🗣️", "tag": "US • Clear", "code": "en-US-AlgiebaNeural"},
}

# --------------------
# Page Setup + Global Styles (No changes here)
# --------------------
def setup_page_config():
    st.set_page_config(page_title="Interview Coach AI", page_icon="📝", layout="centered")

    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #f8f9fa; /* Light background */
            --card-bg: #ffffff; /* White card */
            --text-color: #212529; /* Dark text */
            --primary: #4a55e2; /* Indigo/Blue */
            --primary-light: #e0e7ff;
            --secondary: #6c757d;
            --accent: #ff6b6b; /* Red accent */
            --shadow: rgba(0, 0, 0, 0.08);
            --border-color: rgba(0,0,0,.1);
        }
        /* New Animated Background */
        @keyframes subtle-move {
            0% { background-position: 0% 0%; }
            100% { background-position: 100% 100%; }
        }
        
        /* Force background to be visible on the main page wrapper */
        body {
            font-family: 'Poppins', sans-serif;
            color: var(--text-color);
            background-color: var(--bg);
            background-image: linear-gradient(135deg, #f0f4f8 0%, #e8f0f8 100%);
            background-size: 200% 200%;
            animation: subtle-move 20s ease infinite alternate;
        }

        .block-container { max-width: 800px; padding: 2rem 1rem; }
        h1, h2, h3, h4, h5, h6 { color: var(--text-color); }
        
        /* Main container and cards */
        /* New Card Animation */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .container {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 2.5rem;
            box-shadow: 0 15px 30px var(--shadow);
            margin-bottom: 2rem;
            transition: box-shadow .3s ease;
            animation: fadeIn 0.8s ease-out forwards;
        }
        .container:hover { box-shadow: 0 20px 40px rgba(0,0,0,.12); }

        /* Buttons and inputs */
        .stButton>button {
            border-radius: 999px;
            font-weight: 600;
            padding: 10px 24px;
            transition: all .2s ease;
        }
        .stButton>button:hover { transform: translateY(-1px); }
        
        .stButton>button[kind="primary"] {
            background-color: var(--primary);
            color: white;
            border: none;
        }
        .stButton>button[kind="secondary"] {
            background-color: var(--primary-light);
            color: var(--primary);
            border: none;
        }
        .st-emotion-cache-12oz5g7 {
            padding-top: 2rem !important;
            padding-bottom: 3.5rem !important;
        }

        /* Voice cards */
        .voice-card-container { display: flex; gap: 10px; margin-bottom: 15px; }
        .voice-card {
            flex: 1;
            padding: 14px;
            border-radius: 12px;
            border: 2px solid var(--border-color);
            cursor: pointer;
            transition: all .2s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            background: #f1f3f5;
        }
        .voice-card:hover { border-color: var(--primary); transform: translateY(-2px); }
        .voice-card.selected {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-light);
        }
        .voice-icon { font-size: 2rem; margin-bottom: 8px; }
        .voice-title { font-weight: 600; font-size: 1rem; color: var(--text-color); }
        .voice-tag { font-size: 0.8rem; color: var(--secondary); }

        /* Stepper */
        .stepper { display:flex; gap: 8px; align-items:center; margin: 10px 0 20px 0; justify-content: center; }
        .step {
            display:flex; align-items:center; gap:6px; padding:6px 14px; border-radius:999px;
            background: rgba(0,0,0,.05); color: var(--secondary); font-size:14px; font-weight: 500;
            transition: background .2s ease, color .2s ease;
        }
        .step.active {
            color: white;
            background: var(--primary);
        }

        /* Messages */
        .stChatMessage {
            background: var(--primary-light);
            border-radius: 16px 16px 16px 0;
            padding: 1rem;
            color: var(--text-color);
            margin-bottom: 12px;
        }
        .stChatMessage:last-of-type {
            margin-bottom: 0;
        }
        
        /* Floating Button */
        .fab-wrap{
            position:fixed;
            right: 50%;
            transform: translateX(50%);
            bottom:24px;
            z-index:999;
            width: fit-content;
        }
        .fab {
            background-color: var(--primary);
            color: white;
            border:none;
            border-radius:999px;
            padding:1rem 2rem;
            font-weight:700;
            box-shadow: 0 10px 20px rgba(0,0,0,.2);
            cursor:pointer;
            transition: transform .15s ease, box-shadow .2s ease;
        }
        .fab:hover { transform: translateY(-2px); box-shadow:0 14px 25px rgba(0,0,0,.25); }
    </style>
    """, unsafe_allow_html=True)

# --------------------
# Session State (No changes here)
# --------------------
def initialize_session_state():
    defaults = {
        "interview_started": False,
        "name": "",
        "resume_highlights": "",
        "job_description": "",
        "qa_index": 1,
        "conversations": [],
        "current_question": "",
        "question_spoken": False,
        "awaiting_response": False,
        "processing_audio": False,
        "messages": [],
        "interview_completed": False,
        "max_questions": MAX_QUESTIONS,
        "ai_voice": "Zephyr (Bright)",
        "thanks_message_prepared": False,
        "thanks_message_spoken": False,
        "show_final_results": False,
        "uploaded_resume": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# --------------------
# Helpers
# --------------------
def get_ai_voice_details():
    return {k: {"name": k.split(" ")[0], "code": VOICE_CARDS[k]["code"]} for k in VOICE_CARDS}

def reset_interview_state():
    for key in [
        "interview_started","qa_index","conversations","current_question","question_spoken",
        "awaiting_response","processing_audio","messages","interview_completed",
        "thanks_message_prepared","thanks_message_spoken","show_final_results",
    ]:
        if key in ["qa_index"]:
            st.session_state[key] = 1
        elif key in ["conversations","messages"]:
            st.session_state[key] = []
        else:
            st.session_state[key] = False
    st.session_state["current_question"] = ""

def process_resume_submission(uploaded_resume, job_description):
    with st.spinner("Analyzing your resume and the job description..."):
        resume_content = load_content_streamlit(uploaded_resume)
        name, resume_highlights = extract_resume_info_using_llm(resume_content)
    st.session_state["name"] = name
    st.session_state["resume_highlights"] = resume_highlights
    st.session_state["job_description"] = job_description
    reset_interview_state()
    st.success(f"Great! We've got it. Your name is **{name}**, and we're ready to roll.")

def start_interview():
    st.session_state["interview_started"] = True
    reset_interview_state()
    st.session_state["interview_started"] = True
    ai_voice_details = get_ai_voice_details()
    interviewer_name = ai_voice_details[st.session_state["ai_voice"]]["name"]
    greeting_message = get_ai_greeting_message(st.session_state["name"], interviewer_name=interviewer_name)
    st.session_state["current_question"] = greeting_message
    st.session_state["messages"].append({"role":"assistant","content":greeting_message})

def display_chat_messages():
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def speak_current_question():
    if st.session_state["current_question"] and not st.session_state["question_spoken"]:
        with st.spinner("The AI is asking the next question..."):
            code = get_ai_voice_details()[st.session_state["ai_voice"]]["code"]
            speak_text(st.session_state["current_question"], voice=code)
        st.session_state["question_spoken"] = True
        st.session_state["awaiting_response"] = True
        st.rerun()

def generate_next_question():
    if st.session_state["conversations"]:
        last = st.session_state["conversations"][-1]
        
        # --- FIX: Pass the correct arguments and parse the JSON output ---
        llm_response_str, _ = asyncio.run(analyze_candidate_response_and_generate_new_question(
            last["Question"], last["Candidate Answer"],
            st.session_state["job_description"], st.session_state["resume_highlights"]
        ))
        
        try:
            parsed_response = json.loads(llm_response_str)
            next_q = parsed_response["next_question"]
        except (json.JSONDecodeError, KeyError) as e:
            st.error(f"Error parsing LLM response: {e}. Using a generic question.")
            next_q = "Could you tell me more about your professional experience?"
            
    else:
        next_q = "Tell me about yourself and your experience."
        
    st.session_state["current_question"] = next_q
    st.session_state["messages"].append({"role":"assistant","content":next_q})
    st.session_state["question_spoken"] = False
    st.session_state["awaiting_response"] = False

def process_candidate_response(transcript):
    st.session_state["messages"].append({"role":"user","content":transcript})
    
    # --- FIX: Correctly handle LLM response parsing for both question and feedback ---
    if st.session_state["qa_index"] < st.session_state["max_questions"] - 1:
        llm_response_str, _ = asyncio.run(analyze_candidate_response_and_generate_new_question(
            st.session_state["current_question"], transcript,
            st.session_state["job_description"], st.session_state["resume_highlights"]
        ))
        try:
            parsed_response = json.loads(llm_response_str)
            next_q = parsed_response["next_question"]
            feedback = parsed_response["feedback"]
        except (json.JSONDecodeError, KeyError) as e:
            st.error(f"Error parsing LLM response: {e}. Using a generic question.")
            next_q = "Could you tell me more about your professional experience?"
            feedback = {"score": 5, "feedback": "An error occurred while processing this response."}
    else:
        feedback = asyncio.run(get_feedback_of_candidate_response(
            st.session_state["current_question"], transcript,
            st.session_state["job_description"], st.session_state["resume_highlights"]
        ))
        next_q = None

    st.session_state["conversations"].append({
        "Question": st.session_state["current_question"],
        "Candidate Answer": transcript,
        "Evaluation": feedback["score"],
        "Feedback": feedback["feedback"],
    })

    st.session_state["qa_index"] += 1
    st.session_state["processing_audio"] = False
    st.session_state["awaiting_response"] = False

    if st.session_state["qa_index"] <= st.session_state["max_questions"]:
        if next_q:
            st.session_state["current_question"] = next_q
            st.session_state["messages"].append({"role":"assistant","content":next_q})
            st.session_state["question_spoken"] = False
        st.success("✅ Your answer was recorded! Preparing the next question...")
    else:
        st.session_state["interview_completed"] = True
        prepare_thanks_message()

def prepare_thanks_message():
    if not st.session_state["thanks_message_prepared"]:
        final_note = get_final_thanks_message(st.session_state["name"])
        st.session_state["messages"].append({"role":"assistant","content":final_note})
        st.session_state["thanks_message_prepared"] = True
        st.session_state["qa_index"] -= 1
        st.rerun()

def speak_thanks_message():
    if st.session_state["thanks_message_prepared"] and not st.session_state["thanks_message_spoken"]:
        with st.spinner("Wrapping things up..."):
            code = get_ai_voice_details()[st.session_state["ai_voice"]]["code"]
            speak_text(st.session_state["messages"][-1]["content"], voice=code)
        st.session_state["thanks_message_spoken"] = True
        st.success("🎉 All done! Thanks for your time!")
        st.session_state["show_final_results"] = True
        st.rerun()

def handle_audio_recording():
    if not (st.session_state["awaiting_response"] and not st.session_state["processing_audio"]):
        return
    st.info("🎙️ We're listening! Record your answer now.")
    audio_key = f"audio_input_{st.session_state['qa_index']}_{len(st.session_state['messages'])}"
    audio_data = st.audio_input("Record your answer", key=audio_key)
    if audio_data is not None:
        st.session_state["processing_audio"] = True
        with st.spinner("Transcribing your answer..."):
            name = st.session_state["name"] or "candidate"
            filename = f"audio/{name}/{name}_{st.session_state['qa_index'] + 1}.wav"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "wb") as f:
                f.write(audio_data.read())
            transcript = transcribe_with_speechmatics(filename)
            if transcript and transcript.strip():
                process_candidate_response(transcript)
                st.rerun()
            else:
                st.error("Oops! No speech detected. Could you try recording again?")
            st.session_state["processing_audio"] = False

def display_final_results():
    if not (st.session_state["show_final_results"] and st.session_state["conversations"]):
        return
    with st.spinner("Calculating your final score..."):
        final_score = get_overall_evaluation_score(st.session_state["conversations"])
        now = datetime.now().isoformat()+"Z"
        interview_data = {
            "name": st.session_state["name"],
            "createdAt": now, "updatedAt": now, "id": 1,
            "job_description": st.session_state["job_description"],
            "resume_highlights": st.session_state["resume_highlights"],
            "conversations": st.session_state["conversations"],
            "overall_score": round(final_score, 2),
        }
        save_interview_data(interview_data, candidate_name=st.session_state["name"])

    st.markdown("### 🌟 Your Final Evaluation")
    st.markdown("Here's a quick look at your performance. You did great!")
    st.markdown(f"**Overall Score:** `{final_score:.2f} / 10`")

    for i, conv in enumerate(st.session_state["conversations"], 1):
        with st.expander(f"Question {i} • Score: {conv['Evaluation']}/10"):
            st.write(f"**Q:** {conv['Question']}")
            st.write(f"**Your Answer:** {conv['Candidate Answer']}")
            st.write(f"**Feedback:** {conv['Feedback']}")

    if st.button("🔄 Start a New Interview"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def render_stepper(active_step:int):
    steps = ["Upload Resume", "Set Preferences", "Start Interview"]
    html = '<div class="stepper">' + "".join(
        [f'<div class="step {"active" if i==active_step else ""}">Step {i+1}: {label}</div>' for i, label in enumerate(steps)]
    ) + "</div>"
    st.markdown(html, unsafe_allow_html=True)

# --------------------
# Main Application
# --------------------
def main():
    setup_page_config()
    initialize_session_state()

    st.title("Interview Coach AI")
    st.markdown("Your friendly guide to acing your next interview!")

    # Tabbed Sections
    tabs = st.tabs(["📋 Setup", "📝 Interview", "🏁 Results"])
    
    with tabs[0]:
        render_stepper(0)
        st.header("Step 1: Your Info")
        
        st.markdown("Tell me a bit about the role you're applying for and what you bring to the table. This helps the AI personalize your interview!")
        st.session_state["uploaded_resume"] = st.file_uploader(
            "Upload your resume (PDF)", type=["pdf"], help="Drag & drop supported.",
        )
        jd = st.text_area(
            "Job Description",
            placeholder="Paste the job description here…",
            height=200,
        )
        if st.session_state["uploaded_resume"] and jd.strip():
            st.session_state["job_description"] = jd
            if st.button("🎉 Ready to Analyze!", use_container_width=True):
                process_resume_submission(st.session_state["uploaded_resume"], st.session_state["job_description"])
        else:
            st.info("Psst... You need to upload both a resume and a job description to get started!")

    with tabs[1]:
        render_stepper(1)
        st.header("Step 2: Customize Your Interview")
        st.markdown("Choose how many questions you'd like to practice with and pick the voice of your AI interviewer.")
        st.session_state["max_questions"] = st.slider(
            "Number of questions", 1, 10, st.session_state.get("max_questions", MAX_QUESTIONS)
        )

        st.subheader("Pick a Voice")
        st.markdown("Click on a card to select your interviewer's voice.")
        
        # --- FIX: Replaced custom JS with a reliable Streamlit radio button ---
        voice_options = list(VOICE_CARDS.keys())
        selected_voice = st.radio(
            "Choose a voice", 
            voice_options, 
            index=voice_options.index(st.session_state["ai_voice"]), 
            horizontal=True,
            key="ai_voice_selector"
        )
        st.session_state["ai_voice"] = selected_voice
        st.write("Current voice: ", st.session_state["ai_voice"])

        if st.session_state["name"]:
            st.markdown(f"<div class='container' style='background-color:#d4edda; color:#155724; border-color:#c3e6cb;'>You're all set, <b>{st.session_state['name']}</b>! Press the button below to start.</div>", unsafe_allow_html=True)
            if st.button("🚀 Start Interview!", use_container_width=True):
                start_interview()
                st.rerun()

    with tabs[2]:
        render_stepper(2)
        if st.session_state["interview_started"]:
            st.header("Step 3: Interview Chat")
            st.markdown("This is where the magic happens! Your AI coach will guide you through the interview.")
            
            progress = min(st.session_state["qa_index"] / max(st.session_state["max_questions"], 1), 1.0)
            st.progress(progress)
            
            with st.container():
                display_chat_messages()
                if not st.session_state["interview_completed"]:
                    speak_current_question()
                    handle_audio_recording()
                elif not st.session_state["thanks_message_prepared"]:
                    prepare_thanks_message()
                elif not st.session_state["thanks_message_spoken"]:
                    speak_thanks_message()
                else:
                    display_final_results()
        else:
            st.info("Your interview summary will appear here once you've completed an interview.")

if __name__ == "__main__":
    main()
