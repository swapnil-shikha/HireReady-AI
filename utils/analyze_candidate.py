import asyncio
from typing import Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from utils.llm_call import get_response_from_llm, parse_json_response
from utils.prompts import next_question_generation, feedback_generation

# Thread pool for CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=4)

class InterviewAnalysisError(Exception):
    """Custom exception for interview analysis errors"""
    pass

@lru_cache(maxsize=128)
def _cache_key(prompt: str) -> str:
    """Generate cache key for prompt (optional caching)"""
    return hash(prompt)

async def _make_llm_call_async(prompt: str) -> Dict[str, Any]:
    """
    Make LLM call asynchronously in a thread pool.
    Ensures the response is always a dictionary.
    """
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(executor, get_response_from_llm, prompt)
        parsed = parse_json_response(response)
        if parsed is None:
            parsed = {}
        return parsed
    except Exception as e:
        raise InterviewAnalysisError(f"Failed to get LLM response: {str(e)}")

async def get_next_question(
    previous_question: str, 
    candidate_response: str, 
    resume_highlights: str, 
    job_description: str
) -> str:
    """
    Generate next interview question based on previous interaction.
    """
    try:
        # Ensure inputs are not None
        previous_question = previous_question or ""
        candidate_response = candidate_response or ""
        resume_highlights = resume_highlights or ""
        job_description = job_description or ""

        final_prompt = next_question_generation.format(
            previous_question=previous_question,
            candidate_response=candidate_response,
            resume_highlights=resume_highlights,
            job_description=job_description,
        )
        
        response = await _make_llm_call_async(final_prompt)
        
        if "next_question" not in response:
            raise InterviewAnalysisError("Missing 'next_question' in LLM response")
            
        return response["next_question"]
        
    except Exception as e:
        raise InterviewAnalysisError(f"Question generation failed: {str(e)}")

async def get_feedback_of_candidate_response(
    question: str, 
    candidate_response: str, 
    job_description: str, 
    resume_highlights: str
) -> Dict[str, Any]:
    """
    Generate feedback for candidate's response with safe checks.
    """
    try:
        # Ensure inputs are not None
        question = question or ""
        candidate_response = candidate_response or ""
        job_description = job_description or ""
        resume_highlights = resume_highlights or ""

        final_prompt = feedback_generation.format(
            question=question,
            candidate_response=candidate_response,
            job_description=job_description,
            resume_highlights=resume_highlights,
        )

        # Logging for debugging
        print("Prompt sent to LLM for feedback:", final_prompt)

        response = await _make_llm_call_async(final_prompt)
        print("Raw LLM feedback response:", response)

        if not isinstance(response, dict):
            raise InterviewAnalysisError("LLM response is not a dictionary")

        # Validate required fields
        required_fields = ["feedback", "score"]
        missing_fields = [field for field in required_fields if field not in response]
        if missing_fields:
            raise InterviewAnalysisError(f"Missing fields in response: {missing_fields}")
        
        # Validate score
        try:
            score = float(response["score"])
            if not (0 <= score <= 10):
                print(f"Score {score} is outside expected range 0-10")
        except (ValueError, TypeError):
            raise InterviewAnalysisError(f"Invalid score format: {response['score']}")
        
        return {
            "feedback": response["feedback"],
            "score": score
        }
        
    except Exception as e:
        raise InterviewAnalysisError(f"Feedback generation failed: {str(e)}")

async def analyze_candidate_response_and_generate_new_question(
    question: str, 
    candidate_response: str, 
    job_description: str, 
    resume_highlights: str,
    timeout: float = 30.0
) -> Tuple[str, Dict[str, Any]]:
    """
    Analyze candidate response and generate next question concurrently.
    """
    try:
        # Ensure inputs are safe
        question = question or ""
        candidate_response = candidate_response or ""
        job_description = job_description or ""
        resume_highlights = resume_highlights or ""

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
        raise
    except Exception as e:
        raise InterviewAnalysisError(f"Response analysis failed: {str(e)}")
