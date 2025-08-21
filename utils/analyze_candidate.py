import asyncio
import json
import re
from typing import Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from utils.llm_call import get_response_from_llm
from utils.prompts import next_question_generation, feedback_generation

# Thread pool for CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=4)


class InterviewAnalysisError(Exception):
    """Custom exception for interview analysis errors"""
    pass


@lru_cache(maxsize=128)
def _cache_key(prompt: str) -> str:
    """Generate cache key for prompt (if you want to implement caching)"""
    return str(hash(prompt))


def parse_json_response(response: str) -> dict:
    """
    Try to parse JSON safely from LLM response.
    Extracts the first valid JSON object even if extra text exists.
    """
    if not response or not response.strip():
        return None
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Find first valid JSON object inside messy text
        matches = re.findall(r"\{[\s\S]*?\}", response)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        return None


async def _make_llm_call_async(prompt: str) -> Dict[str, Any]:
    """
    Make LLM call asynchronously by running in thread pool.
    Always returns a dict (may contain fallback).
    """
    try:
        loop = asyncio.get_event_loop()
        raw_response = await loop.run_in_executor(executor, get_response_from_llm, prompt)

        # Debug log
        print("\n=== RAW LLM RESPONSE START ===")
        print(raw_response)
        print("=== RAW LLM RESPONSE END ===\n")

        parsed = parse_json_response(raw_response)

        if parsed is None:
            parsed = {}

        print("PARSED RESPONSE:", parsed)
        return parsed

    except Exception as e:
        print(f"⚠️ LLM call failed: {e}")
        return {}


async def get_next_question(
    previous_question: str,
    candidate_response: str,
    resume_highlights: str,
    job_description: str
) -> str:
    """
    Generate next interview question based on previous interaction.
    Always returns a safe question string.
    """
    try:
        final_prompt = next_question_generation.format(
            previous_question=previous_question,
            candidate_response=candidate_response,
            resume_highlights=resume_highlights,
            job_description=job_description,
        )

        response = await _make_llm_call_async(final_prompt)

        # Fallback if invalid
        if not response or not isinstance(response, dict):
            print("⚠️ Invalid response from LLM, using fallback question.")
            return "Can you tell me more about your problem-solving approach?"

        next_q = response.get("next_question", "").strip()
        if not next_q:
            print("⚠️ Missing 'next_question' in LLM response, using fallback.")
            return "What motivates you to take on challenging projects?"

        return next_q

    except Exception as e:
        print(f"⚠️ Question generation failed: {e}")
        return "Could you describe a challenging situation you faced at work and how you handled it?"


async def get_feedback_of_candidate_response(
    question: str,
    candidate_response: str,
    job_description: str,
    resume_highlights: str
) -> Dict[str, Any]:
    """
    Generate feedback for candidate's response.
    Always returns a feedback dict with feedback + score (0-10).
    """
    final_prompt = feedback_generation.format(
        question=question,
        candidate_response=candidate_response,
        job_description=job_description,
        resume_highlights=resume_highlights,
    )

    try:
        response = await _make_llm_call_async(final_prompt)

        # Try to parse JSON
        if not response or not isinstance(response, dict):
            print("⚠️ Could not parse feedback JSON, trying fallback extraction.")
            # Fallback: at least give default
            return {
                "feedback": "Response was unclear. Try giving more structured, specific examples.",
                "score": 0.0,
            }

        # Extract feedback + score safely
        feedback = response.get("feedback", "").strip()
        if not feedback:
            feedback = "Response was unclear. Try giving more structured, specific examples."

        score_raw = response.get("score", None)
        try:
            score = float(score_raw)
            if not (0 <= score <= 10):
                print(f"⚠️ Score {score} out of range, resetting to 0.")
                score = 0.0
        except (ValueError, TypeError):
            print(f"⚠️ Invalid score format: {score_raw}, defaulting to 0.")
            score = 0.0

        return {"feedback": feedback, "score": score}

    except Exception as e:
        print(f"⚠️ Feedback generation failed: {e}")
        return {
            "feedback": f"Error analyzing response: {str(e)}",
            "score": 0.0,
        }

async def analyze_candidate_response_and_generate_new_question(
    question: str,
    candidate_response: str,
    job_description: str,
    resume_highlights: str,
    timeout: float = 30.0
) -> Tuple[str, Dict[str, Any]]:
    """
    Analyze candidate response and generate next question concurrently.
    Always returns a safe (next_question, feedback).
    """
    try:
        feedback_task = get_feedback_of_candidate_response(
            question, candidate_response, job_description, resume_highlights
        )

        next_question_task = get_next_question(
            question, candidate_response, resume_highlights, job_description
        )

        feedback, next_question = await asyncio.wait_for(
            asyncio.gather(feedback_task, next_question_task),
            timeout=timeout
        )
        return next_question, feedback

    except asyncio.TimeoutError:
        print("⚠️ Analysis timed out.")
        return (
            "Could you elaborate more on your teamwork experience?",
            {"feedback": "Analysis timed out", "score": 0.0}
        )
    except Exception as e:
        print(f"⚠️ Unexpected error during analysis: {e}")
        return (
            "What motivates you to pursue this role?",
            {"feedback": f"Error analyzing response: {str(e)}", "score": 0.0}
        )
