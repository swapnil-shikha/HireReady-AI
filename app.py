import os, certifi, ssl
import streamlit as st
import asyncio
import time
from datetime import datetime
from utils import (
    transcribe_with_speechmatics,
    extract_resume_info_using_llm,
    get_ai_greeting_message,
    get_final_thanks_message,
    speak_text,
    analyze_candidate_response_and_generate_new_question,
    get_feedback_of_candidate_response,
    get_overall_evaluation_score,
    save_interview_data,
    load_content_streamlit,
)

# Force Python / OpenSSL to use certifi's CA bundle
os.environ["SSL_CERT_FILE"] = certifi.where()
ssl._create_default_https_context = ssl.create_default_context

MAX_QUESTIONS = 5

def setup_page_config():
    """Setup page configuration and custom CSS"""
    st.set_page_config(page_title="HireReady AI", layout="wide")

    st.markdown(
        """
    <style>
    /* Overall page background (dark) */
    .stApp {
        background-color: #0d1117;
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Sidebar container (white) */
    .st-emotion-cache-1wv7stn .st-emotion-cache-12tt7y8, .st-emotion-cache-1wv7stn .st-emotion-cache-6qob1p {
        background-color: #ffffff !important;
        color: #0d1117 !important;
    }

    /* Main content container */
    .st-emotion-cache-1wv7stn .st-emotion-cache-1d3923a {
        background-color: #0d1117;
        padding: 2rem;
        border-radius: 12px;
        color: #e0e0e0;
    }

    /* Titles and Headers */
    .st-emotion-cache-1wv7stn h1 {
        color: #00ff66 !important;
        font-weight: 700;
        font-size: 3rem;
        letter-spacing: -1px;
    }
    .st-emotion-cache-1wv7stn h2, .st-emotion-cache-1wv7stn h3 {
        color: #00acee !important;
    }
    .st-emotion-cache-1wv7stn h4 {
        color: #cccccc !important;
    }

    /* Sidebar titles */
    .st-emotion-cache-1wv7stn .st-emotion-cache-1oe5f0g h1 {
        color: #0d1117 !important;
        font-size: 1.5rem;
    }

    /* Buttons */
    .st-emotion-cache-1wv7stn .stButton>button {
        background-color: #00acee;
        color: white;
        border: none;
        padding: 12px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        transition: background-color 0.3s ease, transform 0.2s ease;
    }
    .st-emotion-cache-1wv7stn .stButton>button:hover {
        background-color: #0088cc;
        transform: translateY(-2px);
    }
    .st-emotion-cache-1wv7stn .stButton>button:active {
        transform: translateY(0);
    }

    /* Input fields in sidebar (white background) */
    .st-emotion-cache-1wv7stn .stTextInput>div>div>input, 
    .st-emotion-cache-1wv7stn .stTextArea>div>div>textarea,
    .st-emotion-cache-1wv7stn .stFileUploader {
        background-color: #ffffff !important;
        border: 1px solid #cccccc !important;
        color: #0d1117 !important;
    }

    /* Drag and drop text styling */
    .stFileUploader > div > label > div > div > small {
        color: #555555 !important;
    }

    /* Radio buttons */
    .st-emotion-cache-1wv7stn .stRadio>label>div>div {
        background-color: #f0f2f6;
        border: 1px solid #cccccc;
        border-radius: 8px;
        color: #0d1117;
    }
    .st-emotion-cache-1wv7stn .stRadio>label>div>div:hover {
        background-color: #e9ecef;
    }

    /* Interview-related components (dark theme) */
    .st-emotion-cache-1wv7stn .interview-progress,
    .st-emotion-cache-1wv7stn .audio-section,
    .st-emotion-cache-1wv7stn .st-emotion-cache-uf99v8,
    .st-emotion-cache-1wv7stn .st-emotion-cache-1w03v9r {
        background-color: #1a1a1a;
        border: 1px solid #333333;
        color: #e0e0e0;
    }

    /* Custom classes to match the image precisely */
    .sidebar-title {
        color: #00acee !important;
        font-size: 1.5rem;
        font-weight: bold;
    }

    .main-title-container {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        margin-top: 5rem; /* Adjust to match vertical alignment */
        margin-left: -1rem;
    }
    .main-title {
        color: #00ff66 !important;
        font-size: 3rem;
        font-weight: bold;
    }
    .subtitle {
        color: #ffffff;
        font-size: 1.5rem;
        margin-top: -1rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

def initialize_session_state():
    """Initialize all session state variables"""
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
        "ai_voice": "Alex (Male)",
        "thanks_message_prepared": False,
        "thanks_message_spoken": False,
        "show_final_results": False,
        "submission_processed": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_ai_voice_details():
    """Get AI voice configuration"""
    return {
        "Alex (Male)": {"name": "Alex", "code": "en-US-GuyNeural"},
        "Aria (Female)": {"name": "Aria", "code": "en-US-AriaNeural"},
        "Natasha (Female)": {"name": "Natasha", "code": "en-AU-NatashaNeural"},
        "Sonia (Female)": {"name": "Sonia", "code": "en-GB-SoniaNeural"},
    }

def get_instructions():
    """Get instructions for the user"""
    content = """
    Welcome to your future. Follow these simple steps to start your AI-powered interview.

    1. Upload your Resume: Drop your resume in PDF format. This is your blueprint.
    2. Paste the Job Description: Tell me what role you're aiming for. This is our target.
    3. Start the Interview: Hit the button and let's get this show on the road.
    4. Settings: Adjust the number of questions and select your AI interviewer's voice.
    5. Answer: Speak your truth. The mic is all yours when the light is on.
    6. Review: After the last question, you'll see a full performance breakdown.
    
    Good luck, and may your code be bug-free ✨
    """
    return st.markdown(content)

def render_sidebar():
    """Render sidebar with candidate information and settings"""
    st.sidebar.markdown('<p class="sidebar-title">Your Bio-matrix 🧬</p>', unsafe_allow_html=True)
    st.sidebar.markdown("---")

    uploaded_resume = st.sidebar.file_uploader("Upload your Resume (PDF)", type=["pdf"])
    st.sidebar.markdown("Drag and drop file here")
    st.sidebar.markdown("Limit 200MB per file • PDF")
    
    job_description = st.sidebar.text_area("Paste the Job Description")

    max_questions = st.sidebar.number_input(
        "Maximum number of questions",
        min_value=1,
        max_value=10,
        value=MAX_QUESTIONS,
    )
    st.session_state["max_questions"] = max_questions

    ai_voice = st.sidebar.radio(
        "Select AI Interviewer Voice",
        ["Alex (Male)", "Aria (Female)", "Natasha (Female)", "Sonia (Female)"],
    )
    st.session_state["ai_voice"] = ai_voice

    st.sidebar.markdown("---")
    submit = st.sidebar.button("Access Granted")

    return uploaded_resume, job_description, submit

def process_resume_submission(uploaded_resume, job_description):
    """Process resume and job description submission"""
    with st.spinner("Processing resume..."):
        resume_content = load_content_streamlit(uploaded_resume)
        name, resume_highlights = extract_resume_info_using_llm(resume_content)

    st.session_state["name"] = name
    st.session_state["resume_highlights"] = resume_highlights
    st.session_state["job_description"] = job_description
    st.session_state["submission_processed"] = True

    reset_interview_state()
    st.success(f"Information processed for candidate: {name}")

def reset_interview_state():
    """Reset interview-related session state"""
    interview_keys = [
        "interview_started",
        "qa_index",
        "conversations",
        "current_question",
        "question_spoken",
        "awaiting_response",
        "processing_audio",
        "messages",
        "interview_completed",
        "thanks_message_prepared",
        "thanks_message_spoken",
        "show_final_results",
    ]

    for key in interview_keys:
        if key == "interview_started" or key == "interview_completed":
            st.session_state[key] = False
        elif key in ["qa_index"]:
            st.session_state[key] = 1
        elif key in ["conversations", "messages"]:
            st.session_state[key] = []
        elif key in ["current_question"]:
            st.session_state[key] = ""
        else:
            st.session_state[key] = False

def start_interview():
    """Initialize and start the interview"""
    st.session_state["interview_started"] = True
    reset_interview_state()
    st.session_state["interview_started"] = True

    ai_voice_details = get_ai_voice_details()
    interviewer_name = ai_voice_details[st.session_state["ai_voice"]]["name"]
    greeting_message = get_ai_greeting_message(
        st.session_state["name"], interviewer_name=interviewer_name
    )

    st.session_state["current_question"] = greeting_message
    st.session_state["messages"].append(
        {"role": "assistant", "content": greeting_message}
    )

def display_chat_messages():
    """Display all chat messages from history"""
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def speak_current_question():
    """Speak the current question if not already spoken"""
    if st.session_state["current_question"] and not st.session_state["question_spoken"]:
        with st.spinner("AI Interviewer is speaking..."):
            ai_voice_details = get_ai_voice_details()
            speak_text(
                st.session_state["current_question"],
                voice=ai_voice_details[st.session_state["ai_voice"]]["code"],
            )
        st.session_state["question_spoken"] = True
        st.session_state["awaiting_response"] = True
        st.rerun()

def generate_next_question():
    """Generate and prepare the next question"""
    if st.session_state["conversations"]:
        last_conv = st.session_state["conversations"][-1]
        next_question, _ = asyncio.run(analyze_candidate_response_and_generate_new_question(
            last_conv["Question"],
            last_conv["Candidate Answer"],
            st.session_state["job_description"],
            st.session_state["resume_highlights"],
        ))
    else:
        next_question = "Tell me about yourself and your experience."

    st.session_state["current_question"] = next_question
    st.session_state["messages"].append({"role": "assistant", "content": next_question})
    st.session_state["question_spoken"] = False
    st.session_state["awaiting_response"] = False

def process_candidate_response(transcript):
    """Process candidate's response and move to next state"""
    st.session_state["messages"].append({"role": "user", "content": transcript})

    if st.session_state["qa_index"] < st.session_state["max_questions"]:
        next_question, feedback = asyncio.run(analyze_candidate_response_and_generate_new_question(
            st.session_state["current_question"],
            transcript,
            st.session_state["job_description"],
            st.session_state["resume_highlights"],
        ))
    else:
        feedback = asyncio.run(get_feedback_of_candidate_response(
            st.session_state["current_question"],
            transcript,
            st.session_state["job_description"],
            st.session_state["resume_highlights"],
        ))
        next_question = None

    st.session_state["conversations"].append(
        {
            "Question": st.session_state["current_question"],
            "Candidate Answer": transcript,
            "Evaluation": feedback["score"],
            "Feedback": feedback["feedback"],
        }
    )

    st.session_state["qa_index"] += 1
    st.session_state["processing_audio"] = False
    st.session_state["awaiting_response"] = False

    if next_question:
        st.session_state["current_question"] = next_question
        st.session_state["messages"].append({"role": "assistant", "content": next_question})
        st.session_state["question_spoken"] = False
        st.success("✅ Answer recorded! Preparing next question...")
    else:
        st.session_state["interview_completed"] = True
        prepare_thanks_message()
        st.success("🎉 Interview completed! Thank you for your time.")

def prepare_thanks_message():
    """Prepare and display thanks message"""
    if not st.session_state["thanks_message_prepared"]:
        final_note = get_final_thanks_message(st.session_state["name"])
        st.session_state["messages"].append(
            {"role": "assistant", "content": final_note}
        )
        st.session_state["thanks_message_prepared"] = True
        st.session_state["qa_index"] -= 1
        st.rerun()

def speak_thanks_message():
    """Speak the thanks message"""
    if (
        st.session_state["thanks_message_prepared"]
        and not st.session_state["thanks_message_spoken"]
    ):
        thanks_message = st.session_state["messages"][-1]["content"]
        with st.spinner("AI Interviewer is giving final remarks..."):
            ai_voice_details = get_ai_voice_details()
            speak_text(
                thanks_message,
                voice=ai_voice_details[st.session_state["ai_voice"]]["code"],
            )
        st.session_state["thanks_message_spoken"] = True
        st.session_state["show_final_results"] = True
        st.rerun()

def handle_audio_recording():
    """Handle audio recording and processing"""
    if not (
        st.session_state["awaiting_response"]
        and not st.session_state["processing_audio"]
    ):
        return

    st.markdown("<div class='audio-section'>", unsafe_allow_html=True)
    st.write("🎙️ **Please record your answer**")
    audio_key = f"audio_input_{st.session_state['qa_index']}_{len(st.session_state['messages'])}"
    audio_data = st.file_uploader("Click to record or upload audio", type=["wav", "mp3"], key=audio_key)

    if audio_data is not None:
        st.session_state["processing_audio"] = True
        with st.spinner("Processing your answer..."):
            transcript = transcribe_with_speechmatics(audio_data)
            if transcript and transcript.strip():
                process_candidate_response(transcript)
                st.rerun()
            else:
                st.error("No speech detected in audio. Please try recording again.")
                st.session_state["processing_audio"] = False
    st.markdown("</div>", unsafe_allow_html=True)

def display_final_results():
    """Display final interview results"""
    if (
        not st.session_state["show_final_results"]
        or not st.session_state["conversations"]
    ):
        return

    with st.spinner("Calculating final score..."):
        final_score = get_overall_evaluation_score(st.session_state["conversations"])
        now = datetime.now().isoformat() + "Z"
        interview_data = {
            "name": st.session_state["name"],
            "createdAt": now,
            "updatedAt": now,
            "id": 1,
            "job_description": st.session_state["job_description"],
            "resume_highlights": st.session_state["resume_highlights"],
            "conversations": st.session_state["conversations"],
            "overall_score": round(final_score, 2),
        }
        save_interview_data(interview_data, candidate_name=st.session_state["name"])

    st.subheader("🎉 Interview Results")
    st.markdown(f"**Candidate:** {st.session_state['name']}")
    st.markdown(f"**Overall Score:** **<span style='color: #00ff66;'>{final_score:.2f}/10</span>**", unsafe_allow_html=True)

    st.subheader("Detailed Interview Summary")
    for i, conv in enumerate(st.session_state["conversations"], 1):
        with st.expander(f"Question {i} (Score: {conv['Evaluation']}/10)"):
            st.write(f"**Q:** {conv['Question']}")
            st.write(f"**A:** {conv['Candidate Answer']}")
            st.write(f"**Feedback:** {conv['Feedback']}")

    if st.button("Start New Interview"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def render_interview_progress():
    """Render interview progress indicator"""
    if st.session_state.get("interview_started", False):
        progress_text = f"Question {st.session_state['qa_index']} of {st.session_state['max_questions']}"
        st.markdown(
            f'<div class="interview-progress"><strong>{progress_text}</strong></div>',
            unsafe_allow_html=True,
        )

def main():
    """Main application function"""
    setup_page_config()
    initialize_session_state()

    st.sidebar.markdown('<p class="sidebar-title">Your Bio-matrix 🧬</p>', unsafe_allow_html=True)
    st.sidebar.header("Candidate Information")
    st.sidebar.markdown("---")

    if not st.session_state["submission_processed"]:
        uploaded_resume, job_description, submit = render_sidebar()
        if submit and uploaded_resume and job_description:
            process_resume_submission(uploaded_resume, job_description)
            st.rerun()

    st.markdown(
        f"""
        <div class="main-title-container">
            <h1 class="main-title">HireReady AI</h1>
            <h2 class="subtitle">Ready to Launch?</h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if st.session_state.get("submission_processed", False) and not st.session_state.get("interview_started", False):
        st.markdown("---")
        if st.button("Start Interview", use_container_width=True):
            start_interview()
            st.rerun()
    
    if st.session_state.get("interview_started", False):
        render_interview_progress()
        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("Interview Chat")
        display_chat_messages()

        if not st.session_state["interview_completed"]:
            speak_current_question()
            handle_audio_recording()
        elif not st.session_state["thanks_message_prepared"]:
            prepare_thanks_message()
            speak_thanks_message()
        elif st.session_state["thanks_message_spoken"]:
            display_final_results()

    st.sidebar.markdown("---")

if __name__ == "__main__":
    main()