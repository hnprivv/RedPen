"""
Structural regression checks against the real Gemini API.

These do NOT assert on exact wording (the model's output isn't deterministic),
only on the contract app.py's rendering depends on: exact section headers,
in order, plus the word-count ceilings stated in the prompts.

Excluded from the default `pytest` run (see pytest.ini). Run explicitly with:
    pytest -m live
whenever the prompts, model name, or temperature change.
"""
import os

import pytest
from google import genai
from google.genai import types

from core import PROMPT_CV_ONLY, PROMPT_CV_WITH_JD, extract_text_from_docx

pytestmark = pytest.mark.live

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "..", "test-docs")
SAMPLE_JD = "Backend Engineer, 3+ years Python, REST APIs, PostgreSQL, AWS."


def load_cv_text() -> str:
    with open(os.path.join(FIXTURE_DIR, "CV-1.docx"), "rb") as f:
        return extract_text_from_docx(f.read())


def get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set in environment")
    return genai.Client(api_key=api_key)


def run_review(system_prompt: str, contents: str) -> str:
    client = get_client()
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.4,
            max_output_tokens=3000,
        ),
    )
    return response.text


def test_cv_only_response_has_expected_headers_and_length():
    cv_text = load_cv_text()
    feedback = run_review(PROMPT_CV_ONLY, f"Please review this CV:\n\n{cv_text}")

    for header in ["## Overall Impression", "## Strengths", "## Areas for Improvement", "## Quick Win"]:
        assert header in feedback

    assert len(feedback.split()) <= 450 * 1.15  # allow small model overshoot


def test_cv_with_jd_response_has_expected_headers_and_length():
    cv_text = load_cv_text()
    contents = f"Job Description:\n{SAMPLE_JD}\n\nCV:\n{cv_text}\n\nPlease review this CV against the job description."
    feedback = run_review(PROMPT_CV_WITH_JD, contents)

    for header in [
        "## Overall Impression", "## Strengths", "## Job Fit",
        "## Gaps", "## Areas for Improvement", "## Quick Win",
    ]:
        assert header in feedback

    assert len(feedback.split()) <= 600 * 1.15


def test_cv_only_addresses_user_directly():
    cv_text = load_cv_text()
    feedback = run_review(PROMPT_CV_ONLY, f"Please review this CV:\n\n{cv_text}")
    lowered = feedback.lower()
    assert "the candidate" not in lowered
