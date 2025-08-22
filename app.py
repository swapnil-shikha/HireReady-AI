import os, certifi, ssl

# Force Python / OpenSSL to use certifi's CA bundle
os.environ["SSL_CERT_FILE"] = certifi.where()
ssl._create_default_https_context = ssl.create_default_context

import streamlit as st
import asyncio
import os
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

MAX_QUESTIONS = 5


# Configuration and Styling
def setup_page_config():
    """Setup page configuration and custom CSS"""
    st.set_page_config(page_title="HireReady AI", layout="wide")

    st.markdown(
    """
<style>
/* Define a modern, clean white theme with cool blue/teal accents */
:root {
    --white-bg: #FFFFFF; /* Pure white background */
    --light-gray: #F0F2F6; /* A very light gray for contrast */
    --medium-gray: #C4C4C4; /* For borders or minor elements */
    --text-color: #333333; /* Dark gray for main text readability */
    --accent-teal: #3AB7B5; /* The professional teal accent color */
    --soft-red: #D64545; /* A muted red for errors/warnings */
    --shadow-color: rgba(58, 183, 181, 0.2); /* Softened glow for accents */
}

/* Core App Background (all elements) */
body, .stApp, .css-h5rg8b {
    color: var(--text-color);
    background-color: var(--white-bg);
}

/* Streamlit Main Content */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    background-color: var(--light-gray);
    color: var(--text-color);
    border-radius: 10px;
    padding: 20px;
    border: 1px solid var(--accent-teal);
    box-shadow: 0 0 10px var(--shadow-color);
}

/* Sidebar Styling */
.css-1d391kg, .css-1l02z9c {
    background-color: var(--light-gray);
    color: var(--text-color);
    border-radius: 10px;
    padding: 15px;
    border: 1px solid var(--accent-teal);
    box-shadow: 0 0 10px var(--shadow-color);
}
.css-1l02z9c .css-1cpx97d {
    background-color: var(--accent-teal);
    color: var(--white-bg);
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    box-shadow: 0 0 5px var(--accent-teal);
    transition: transform 0.2s, box-shadow 0.2s;
}
.css-1l02z9c .css-1cpx97d:hover {
    transform: scale(1.02);
    box-shadow: 0 0 15px var(--accent-teal);
}

/* General Button Styling */
.stButton>button {
    background-color: var(--accent-teal);
    color: var(--white-bg);
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    box-shadow: 0 0 5px var(--accent-teal);
    transition: transform 0.2s, box-shadow 0.2s;
}
.stButton>button:hover {
    transform: scale(1.02);
    box-shadow: 0 0 15px var(--accent-teal);
}

/* Text Areas & Inputs */
.st-ag, .st-d9 {
    background-color: var(--light-gray);
    color: var(--text-color);
    border: 1px solid var(--accent-teal);
    border-radius: 8px;
    padding: 10px;
    box-shadow: 0 0 3px var(--accent-teal) inset;
}
.st-ag textarea, .st-d9 input {
    color: var(--text-color);
}
.st-ag textarea:focus, .st-d9 input:focus {
    outline: none;
    border-color: var(--accent-teal);
    box-shadow: 0 0 5px var(--accent-teal);
}

/* Chat Messages */
.chat-wrap {
    display: flex;
    flex-direction: column;
}

.chat-bubble {
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 15px;
    max-width: 80%;
    word-wrap: break-word;
}

.chat-bubble.ai {
    align-self: flex-start;
    background-color: var(--light-gray);
    color: var(--text-color);
    border: 2px solid var(--accent-teal);
}

.chat-bubble.user {
    align-self: flex-end;
    background-color: var(--accent-teal);
    color: var(--white-bg);
    border: 2px solid var(--accent-teal);
}

/* Headers */
h1, h2, h3, h4, h5, h6 {
    color: var(--accent-teal);
    text-shadow: none; /* No shadow for a cleaner look */
}

/* Spinner */
.stSpinner>div>div {
    border-top-color: var(--accent-teal);
}

/* Progress & Success messages */
.interview-progress {
    background-color: var(--light-gray);
    color: var(--text-color);
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 20px;
    text-align: center;
    border: 2px solid var(--accent-teal);
    box-shadow: 0 0 5px var(--accent-teal);
}
.st-success {
    background-color: var(--light-gray);
    color: var(--accent-teal);
    border: 1px solid var(--accent-teal);
    box-shadow: 0 0 5px var(--accent-teal);
    border-radius: 8px;
}
.st-error {
    background-color: var(--light-gray);
    color: var(--soft-red);
    border: 1px solid var(--soft-red);
    border-radius: 8px;
}

/* Expander */
.st-ea {
    border: 1px solid var(--accent-teal);
    border-radius: 10px;
    background-color: var(--light-gray);
}

/* Sidebar background again for emphasis */
[data-testid="stSidebar"] {
    background-color: var(--light-gray) !important;
    color: var(--text-color) !important;
}

/* Sidebar labels & headers */
[data-testid="stSidebar"] .css-1p0dtai,
[data-testid="stSidebar"] .css-16idsys,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
    color: var(--text-color) !important;
    font-weight: 500;
}

/* Input fields */
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] select {
    background-color: var(--white-bg) !important;
    color: var(--text-color) !important;
    border: 1px solid var(--accent-teal) !important;
    border-radius: 8px;
}

/* Dropdown / selectbox arrow */
[data-testid="stSidebar"] svg {
    fill: var(--accent-teal) !important;
}

/* Card Styling */
.card {
    background-color: var(--light-gray);
    border-radius: 10px;
    padding: 20px;
    border: 1px solid var(--accent-teal);
    box-shadow: 0 0 10px var(--shadow-color);
    margin-bottom: 20px;
}
</style>
""",
    unsafe_allow_html=True,
)
# Navbar (injected)
    st.markdown(
        """
        <div class="custom-navbar">
            <div class="brand">
            <h2>
                <div class="logo" style="color:var(--text-color);">🤖 HireReady AI</div></h2>
                <h5>
                <div class="subtitle" style="color:var(--text-color);">Practice • Feedback • Improve</div></h5>
            </div>
            <div class="nav-links">
                <a href="#instructions" style="color:var(--text-color);">Instructions</a>
                <a href="#interview-chat" style="color:var(--text-color);">Interview</a>
                <a href="#results" style="color:var(--text-color);">Results</a>
            </div>
        </div>
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
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_ai_voice_details():
    """Get AI voice configuration"""
    return {
        "Tony Stark (Male)": {"name": "Tony Stark", "code": "en-US-GuyNeural"},
        "Guen(Female)": {"name": "Guen", "code": "en-US-AriaNeural"},
        "Natasha (Female)": {"name": "Natasha", "code": "en-AU-NatashaNeural"},
        "Moana (Female)": {"name": "Moana", "code": "en-GB-SoniaNeural"},
    }


def get_instructions():
    """Get instructions for the user"""
    content = """
    <div id="instructions" class="card">
    <h3 style="color:var(--accent-teal); margin-top:0">How to use HireReady AI</h3>
    <ol style="color:var(--text-color);">
      <li>Upload your resume (PDF).</li>
      <li>Paste the job description in the sidebar.</li>
      <li>Set maximum questions and choose voice.</li>
      <li>Start interview and answer via the audio recorder.</li>
      <li>Receive feedback and overall score after completion.</li>
    </ol>
    </div>
    """
    return st.markdown(content, unsafe_allow_html=True)


def render_sidebar():
    """Render sidebar with candidate information and styled settings"""
    st.sidebar.markdown("<h3 style='color:var(--accent-teal)'>Candidate Information</h3>", unsafe_allow_html=True)

    # File upload
    uploaded_resume = st.sidebar.file_uploader("Upload your Resume (PDF)", type=["pdf"]) 

    # Job description
    job_description = st.sidebar.text_area("Paste the Job Description", height=150)

    # Settings
    max_questions = st.sidebar.number_input(
        "Maximum number of questions",
        min_value=1,
        max_value=10,
        value=MAX_QUESTIONS,
    )
    st.session_state["max_questions"] = max_questions

    ai_voice = st.sidebar.radio(
        "Select AI Interviewer Voice",
        ["Tony Stark (Male)", "Guen (Female)", "Natasha (Female)", "Moana (Female)"],
    )
    st.session_state["ai_voice"] = ai_voice

    st.sidebar.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    submit = st.sidebar.button("Submit")

    # Small footer in sidebar
    st.sidebar.markdown("<hr style='border-color:var(--accent-teal)'/>", unsafe_allow_html=True)
    st.sidebar.markdown("<div style='font-size:12px;color:var(--text-color)'>Theme: Professional • Navy • Teal</div>", unsafe_allow_html=True)

    return uploaded_resume, job_description, submit


def process_resume_submission(uploaded_resume, job_description):
    """Process resume and job description submission"""
    with st.spinner("Processing resume..."):
        resume_content = load_content_streamlit(uploaded_resume)
        name, resume_highlights = extract_resume_info_using_llm(resume_content)

    # Store in session state
    st.session_state["name"] = name
    st.session_state["resume_highlights"] = resume_highlights
    st.session_state["job_description"] = job_description

    # Reset interview state
    reset_interview_state()

    st.success(f"Candidate Name: {name}")


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
    st.session_state["interview_started"] = True  # Reset above sets this to False

    # Get greeting message
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
    """Display all chat messages from history using styled bubbles"""
    if not st.session_state.get("messages"):
        return

    html = ['<div id="interview-chat" class="card">', '<div class="chat-wrap">']
    for message in st.session_state["messages"]:
        role = message.get("role", "assistant")
        content = message.get("content", "")
        # sanitize small bit - Streamlit will escape by default in st.markdown unless unsafe
        if role == "assistant":
            html.append(f'<div class="chat-bubble ai">{content}</div>')
        else:
            html.append(f'<div class="chat-bubble user">{content}</div>')
    html.append('</div>')
    html.append('</div>')

    st.markdown('\n'.join(html), unsafe_allow_html=True)


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
    # Add candidate's answer to chat
    st.session_state["messages"].append({"role": "user", "content": transcript})

    # Generate feedback for this response
    if st.session_state["qa_index"] < st.session_state["max_questions"] - 1:
        # Not the last question - generate next question and feedback
        next_question, feedback = asyncio.run(analyze_candidate_response_and_generate_new_question(
            st.session_state["current_question"],
            transcript,
            st.session_state["job_description"],
            st.session_state["resume_highlights"],
        ))
    else:
        # Last question - only generate feedback
        feedback = asyncio.run(get_feedback_of_candidate_response(
            st.session_state["current_question"],
            transcript,
            st.session_state["job_description"],
            st.session_state["resume_highlights"],
        ))

    # Store conversation
    st.session_state["conversations"].append(
        {
            "Question": st.session_state["current_question"],
            "Candidate Answer": transcript,
            "Evaluation": feedback["score"],
            "Feedback": feedback["feedback"],
        }
    )

    # Move to next question or complete interview
    st.session_state["qa_index"] += 1
    st.session_state["processing_audio"] = False
    st.session_state["awaiting_response"] = False

    if st.session_state["qa_index"] <= st.session_state["max_questions"]:
        # Prepare next question
        generate_next_question()
        st.success("✅ Answer recorded! Preparing next question...")
    else:
        # Interview completed - prepare thanks message
        st.session_state["interview_completed"] = True
        prepare_thanks_message()


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

        # Get the last message (thanks message)
        thanks_message = st.session_state["messages"][-1]["content"]

        with st.spinner("AI Interviewer is giving final remarks..."):
            ai_voice_details = get_ai_voice_details()
            speak_text(
                thanks_message,
                voice=ai_voice_details[st.session_state["ai_voice"]]["code"],
            )

        st.session_state["thanks_message_spoken"] = True
        st.success("🎉 Interview completed! Thank you for your time.")

        # Now show final results
        st.session_state["show_final_results"] = True
        st.rerun()


def handle_audio_recording():
    """Handle audio recording and processing"""
    if not (
        st.session_state["awaiting_response"]
        and not st.session_state["processing_audio"]
    ):
        return

    st.markdown('<div class="audio-section card">', unsafe_allow_html=True)
    st.markdown("**🎙️ Please record your answer to the question above**")

    audio_key = f"audio_input_{st.session_state['qa_index']}_{len(st.session_state['messages'])}"
    audio_data = st.audio_input("Record your answer", key=audio_key)

    if audio_data is not None:
        st.session_state["processing_audio"] = True

        with st.spinner("Processing your answer..."):
            # Save audio file
            name = st.session_state["name"]
            filename = f"audio/{name}/{name}_{st.session_state['qa_index'] + 1}.wav"
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            with open(filename, "wb") as f:
                f.write(audio_data.read())

            # Transcribe audio
            transcript = transcribe_with_speechmatics(filename)

            if transcript and transcript.strip():
                process_candidate_response(transcript)
                st.rerun()
            else:
                st.error("No speech detected in audio. Please try recording again.")
                st.session_state["processing_audio"] = False

    st.markdown('</div>', unsafe_allow_html=True)


def display_final_results():
    """Display final interview results"""
    if (
        not st.session_state["show_final_results"]
        or not st.session_state["conversations"]
    ):
        return

    with st.spinner("Calculating final score..."):
        final_score = get_overall_evaluation_score(st.session_state["conversations"])

        # Save interview data
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

    # Display results
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎉 Interview Results")
    st.markdown(f"**Candidate:** {st.session_state['name']}")
    st.markdown(f"**Overall Score:** {final_score:.2f}/10")

    # Show detailed summary
    st.subheader("Detailed Interview Summary")
    for i, conv in enumerate(st.session_state["conversations"], 1):
        with st.expander(f"Question {i} (Score: {conv['Evaluation']}/10)"):
            st.write(f"**Q:** {conv['Question']}")
            st.write(f"**A:** {conv['Candidate Answer']}")
            st.write(f"**Feedback:** {conv['Feedback']}")

    # New interview option
    if st.button("Start New Interview"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def render_interview_progress():
    """Render interview progress indicator"""
    if st.session_state.get("interview_started", False):
        progress_text = f"Question {st.session_state['qa_index']} of {st.session_state['max_questions']}"
        st.markdown(
            f'<div class="interview-progress">{progress_text}</div>',
            unsafe_allow_html=True,
        )


def main():
    """Main application function"""
    # Setup
    setup_page_config()
    initialize_session_state()

    # Header and instructions
    if not st.session_state["interview_started"]:
        get_instructions()

    # Sidebar
    uploaded_resume, job_description, submit = render_sidebar()

    # Process submission
    if submit and uploaded_resume and job_description:
        # clear instructions card
        st.empty()
        process_resume_submission(uploaded_resume, job_description)

    # Start interview button (prominent) - placed in main area for visibility
    if st.session_state["name"] and not st.session_state["interview_started"]:
        if st.button("Start Interview", key="start_interview_btn"):
            start_interview()
            st.rerun()

    # Interview section
    if st.session_state.get("interview_started", False):
        render_interview_progress()

        # Show chat history
        st.subheader("Interview Chat")
        display_chat_messages()

        # Handle different interview states
        if not st.session_state["interview_completed"]:
            # Active interview
            speak_current_question()
            handle_audio_recording()
        elif not st.session_state["thanks_message_prepared"]:
            # Interview just completed - prepare thanks
            prepare_thanks_message()
        elif not st.session_state["thanks_message_spoken"]:
            # Thanks message prepared but not spoken
            speak_thanks_message()
        else:
            # Everything done - show results
            display_final_results()


if __name__ == "__main__":
    main()