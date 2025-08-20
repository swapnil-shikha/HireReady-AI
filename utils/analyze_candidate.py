import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Dict, Any, Tuple

from utils.llm_call import get_response_from_llm, parse_json_response
from utils.prompts import next_question_generation, feedback_generation

executor = ThreadPoolExecutor(max_workers=4)

class InterviewAnalysisError(Exception):
    """Custom exception for interview analysis errors"""
    pass

@lru_cache(maxsize=128)
def _cache_key(prompt: str) -> str:
    return hash(prompt)

async def _make_llm_call_async(prompt: str) -> Dict[str, Any]:
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(executor, get_response_from_llm, prompt)
        return parse_json_response(response)
    except Exception as e:
        raise InterviewAnalysisError(f"Failed to get LLM response: {str(e)}")


async def get_next_question(previous_question: str, candidate_response: str,
                            resume_highlights: str, job_description: str) -> str:
    try:
        prompt = next_question_generation.format(
            previous_question=previous_question,
            candidate_response=candidate_response,
            resume_highlights=resume_highlights,
            job_description=job_description
        )
        response = await _make_llm_call_async(prompt)
        if "next_question" not in response:
            raise InterviewAnalysisError("Missing 'next_question' in LLM response")
        return response["next_question"]
    except Exception as e:
        raise InterviewAnalysisError(f"Question generation failed: {str(e)}")


async def get_feedback_of_candidate_response(question: str, candidate_response: str,
                                             job_description: str, resume_highlights: str) -> Dict[str, Any]:
    try:
        prompt = feedback_generation.format(
            question=question,
            candidate_response=candidate_response,
            job_description=job_description,
            resume_highlights=resume_highlights
        )
        response = await _make_llm_call_async(prompt)
        if "feedback" not in response or "score" not in response:
            raise InterviewAnalysisError("Invalid feedback response")
        try:
            score = float(response["score"])
        except (ValueError, TypeError):
            score = 0
        return {"feedback": response["feedback"], "score": score}
    except Exception as e:
        raise InterviewAnalysisError(f"Feedback generation failed: {str(e)}")


async def analyze_candidate_response_and_generate_new_question(question: str, candidate_response: str,
                                                               job_description: str, resume_highlights: str,
                                                               timeout: float = 30.0) -> Tuple[str, Dict[str, Any]]:
    try:
        feedback_task = get_feedback_of_candidate_response(question, candidate_response, job_description, resume_highlights)
        next_question_task = get_next_question(question, candidate_response, resume_highlights, job_description)
        feedback, next_question = await asyncio.wait_for(
            asyncio.gather(feedback_task, next_question_task),
            timeout=timeout
        )
        return next_question, feedback
    except asyncio.TimeoutError:
        raise
    except Exception as e:
        raise InterviewAnalysisError(f"Response analysis failed: {str(e)}")
