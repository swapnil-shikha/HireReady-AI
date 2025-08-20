from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime
import streamlit as st

# Load environment variables
load_dotenv()
print("Mistral API Key loaded:", os.getenv("MISTRAL_API_KEY"))

# Import utilities
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
from utils.analyze_candidate import InterviewAnalysisError

MAX_QUESTIONS = 5

# ------------------------ Helper Functions ------------------------

def safe_async_run(coro):
    """Run async coroutine safely even if event loop is running"""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


def setup_page_config():
    st.set_page_config(page_title="AI Interview App", layout="wide")
    st.markdown("""
    <style>
    .audio-section {background-color: #f8f9fa; border-radius: 10px; padding: 20px; margin-top: 20px; text-align: center; border: 2px solid #e9ecef;}
    .interview-progress {background-color: #e8f5e8; border-radius: 10px; padding: 15px; margin-bottom: 20px; text-align: center;}
    </style>
    """, unsafe_allow_html=True)


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
        "ai_voice": "Alex (Male)",
        "thanks_message_prepared": False,
        "thanks_message_spoken": False,
        "show_final_results": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_ai_voice_details():
    return {
        "Alex (Male)": {"name": "Alex", "code": "en-US-GuyNeural"},
        "Aria (Female)": {"name": "Aria", "code": "en-US-AriaNeural"},
        "Natasha (Female)": {"name": "Natasha", "code": "en-AU-NatashaNeural"},
        "Sonia (Female)": {"name": "Sonia", "code": "en-GB-SoniaNeural"},
    }


def get_instructions():
    st.markdown("""
    #### Please follow these steps to use the AI Interview App:
    1. Upload Resume in PDF format.
    2. Paste the Job Description.
    3. Click "Start Interview".
    4. Maximum Questions can be set (default 5).
    5. Select AI Voice (default Alex).
    6. Answer questions and review results.
    """)


def render_sidebar():
    st.sidebar.title("Candidate Information")
    uploaded_resume = st.sidebar.file_uploader("Upload your Resume (PDF)", type=["pdf"])
    job_description = st.sidebar.text_area("Paste the Job Description")
    max_questions = st.sidebar.number_input("Maximum number of questions", min_value=1, max_value=10, value=MAX_QUESTIONS)
    st.session_state["max_questions"] = max_questions
    ai_voice = st.sidebar.radio("Select AI Interviewer Voice", ["Alex (Male)", "Aria (Female)", "Natasha (Female)", "Sonia (Female)"])
    st.session_state["ai_voice"] = ai_voice
    submit = st.sidebar.button("Submit")
    return uploaded_resume, job_description, submit


def reset_interview_state():
    keys = ["interview_started", "qa_index", "conversations", "current_question",
            "question_spoken", "awaiting_response", "processing_audio", "messages",
            "interview_completed", "thanks_message_prepared", "thanks_message_spoken",
            "show_final_results"]
    for key in keys:
        if key in ["qa_index"]: st.session_state[key] = 1
        elif key in ["conversations", "messages"]: st.session_state[key] = []
        else: st.session_state[key] = False
    st.session_state["current_question"] = ""


def process_resume_submission(uploaded_resume, job_description):
    with st.spinner("Processing resume..."):
        resume_content = load_content_streamlit(uploaded_resume)
        name, resume_highlights = extract_resume_info_using_llm(resume_content)
    st.session_state["name"] = name
    st.session_state["resume_highlights"] = resume_highlights
    st.session_state["job_description"] = job_description
    reset_interview_state()
    st.success(f"Candidate Name: {name}")


def start_interview():
    reset_interview_state()
    st.session_state["interview_started"] = True
    ai_voice_details = get_ai_voice_details()
    greeting_message = get_ai_greeting_message(st.session_state["name"], interviewer_name=ai_voice_details[st.session_state["ai_voice"]]["name"])
    st.session_state["current_question"] = greeting_message
    st.session_state["messages"].append({"role": "assistant", "content": greeting_message})


def display_chat_messages():
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def speak_current_question():
    if st.session_state["current_question"] and not st.session_state["question_spoken"]:
        with st.spinner("AI is speaking..."):
            speak_text(st.session_state["current_question"], voice=get_ai_voice_details()[st.session_state["ai_voice"]]["code"])
        st.session_state["question_spoken"] = True
        st.session_state["awaiting_response"] = True
        st.rerun()


# ------------------ Core Interview Flow ------------------

def generate_next_question():
    """Generate next question safely"""
    try:
        if st.session_state["conversations"]:
            last_conv = st.session_state["conversations"][-1]
            next_question, _ = safe_async_run(
                analyze_candidate_response_and_generate_new_question(
                    question=last_conv["Question"],
                    candidate_response=last_conv["Candidate Answer"],
                    job_description=st.session_state["job_description"],
                    resume_highlights=st.session_state["resume_highlights"],
                    timeout=30.0
                )
            )
        else:
            next_question = "Tell me about yourself and your experience."
        st.session_state["current_question"] = next_question
        st.session_state["messages"].append({"role": "assistant", "content": next_question})
        st.session_state["question_spoken"] = False
        st.session_state["awaiting_response"] = True
    except Exception as e:
        st.error(f"Failed to generate next question: {str(e)}")


def process_candidate_response(transcript: str):
    st.session_state["messages"].append({"role": "user", "content": transcript})
    try:
        if st.session_state["qa_index"] < st.session_state["max_questions"]:
            next_question, feedback = safe_async_run(
                analyze_candidate_response_and_generate_new_question(
                    question=st.session_state["current_question"],
                    candidate_response=transcript,
                    job_description=st.session_state["job_description"],
                    resume_highlights=st.session_state["resume_highlights"],
                    timeout=30.0
                )
            )
        else:
            feedback = safe_async_run(
                get_feedback_of_candidate_response(
                    question=st.session_state["current_question"],
                    candidate_response=transcript,
                    job_description=st.session_state["job_description"],
                    resume_highlights=st.session_state["resume_highlights"]
                )
            )
            next_question = None

        if feedback is None or "feedback" not in feedback or "score" not in feedback:
            feedback = {"feedback": "N/A", "score": 0}

        st.session_state["conversations"].append({
            "Question": st.session_state["current_question"],
            "Candidate Answer": transcript,
            "Evaluation": feedback.get("score", 0),
            "Feedback": feedback.get("feedback", "N/A")
        })

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

    except Exception as e:
        st.error(f"Error processing response: {str(e)}")
        st.session_state["processing_audio"] = False


def handle_audio_recording():
    if not (st.session_state["awaiting_response"] and not st.session_state["processing_audio"]):
        return
    st.write("**🎙️ Please record your answer to the question above**")
    audio_key = f"audio_input_{st.session_state['qa_index']}_{len(st.session_state['messages'])}"
    audio_data = st.audio_input("Record your answer", key=audio_key)
    if audio_data is None:
        return
    st.session_state["processing_audio"] = True
    with st.spinner("Processing your answer..."):
        name = st.session_state["name"] or "candidate"
        filename = f"audio/{name}/{name}_{st.session_state['qa_index'] + 1}.wav"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "wb") as f:
            f.write(audio_data.read())
        transcript = transcribe_with_speechmatics(filename)
        if not transcript or transcript.strip() == "":
            st.error("No speech detected. Please try recording again.")
            st.session_state["processing_audio"] = False
            return
        process_candidate_response(transcript)


def prepare_thanks_message():
    if not st.session_state["thanks_message_prepared"]:
        final_note = get_final_thanks_message(st.session_state["name"])
        st.session_state["messages"].append({"role": "assistant", "content": final_note})
        st.session_state["thanks_message_prepared"] = True
        st.rerun()


def speak_thanks_message():
    if st.session_state["thanks_message_prepared"] and not st.session_state["thanks_message_spoken"]:
        thanks_message = st.session_state["messages"][-1]["content"]
        with st.spinner("AI Interviewer is giving final remarks..."):
            speak_text(thanks_message, voice=get_ai_voice_details()[st.session_state["ai_voice"]]["code"])
        st.session_state["thanks_message_spoken"] = True
        st.session_state["show_final_results"] = True
        st.rerun()


def display_final_results():
    if not st.session_state["show_final_results"] or not st.session_state["conversations"]:
        return
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
    st.markdown(f"**Overall Score:** {final_score:.2f}/10")
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
    if st.session_state.get("interview_started", False):
        progress_text = f"Question {st.session_state['qa_index']} of {st.session_state['max_questions']}"
        st.markdown(f'<div class="interview-progress"><strong>{progress_text}</strong></div>', unsafe_allow_html=True)


# ------------------------ Main App ------------------------
def main():
    setup_page_config()
    initialize_session_state()
    st.title("🤖 AI Interview System")

    insturctions = st.empty()
    if not st.session_state["interview_started"]:
        insturctions = get_instructions()

    uploaded_resume, job_description, submit = render_sidebar()
    if submit and uploaded_resume and job_description:
        insturctions.empty()
        process_resume_submission(uploaded_resume, job_description)

    if st.session_state["name"] and not st.session_state["interview_started"]:
        if st.button("Start Interview"):
            start_interview()
            st.rerun()

    if st.session_state.get("interview_started", False):
        render_interview_progress()
        st.subheader("Interview Chat")
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


if __name__ == "__main__":
    main()
