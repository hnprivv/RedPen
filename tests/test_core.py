import os

import pytest

from core import (
    PROMPT_CV_ONLY,
    PROMPT_CV_WITH_JD,
    SECTION_CONFIG,
    select_prompt,
    md_to_html,
    parse_feedback,
    extract_text_from_docx,
    build_error_message,
)

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "..", "test-docs")


def load_fixture(name: str) -> bytes:
    with open(os.path.join(FIXTURE_DIR, name), "rb") as f:
        return f.read()


# --- select_prompt ---

def test_select_prompt_no_jd_returns_cv_only():
    assert select_prompt("") == PROMPT_CV_ONLY
    assert select_prompt("   ") == PROMPT_CV_ONLY


def test_select_prompt_with_jd_returns_cv_with_jd():
    assert select_prompt("Senior Backend Engineer role...") == PROMPT_CV_WITH_JD


# --- md_to_html ---

def test_md_to_html_bold():
    assert md_to_html("**Strong**") == '<p style="margin:0.4rem 0;"><strong>Strong</strong></p>'


def test_md_to_html_bullet_list_wraps_in_ul():
    html = md_to_html("- one\n- two")
    assert html.startswith('<ul')
    assert html.endswith('</ul>')
    assert '<li style="margin-bottom:0.5rem;">one</li>' in html
    assert '<li style="margin-bottom:0.5rem;">two</li>' in html


def test_md_to_html_closes_list_on_blank_line():
    html = md_to_html("- one\n\nplain paragraph")
    assert '</ul>' in html
    assert '<p style="margin:0.4rem 0;">plain paragraph</p>' in html
    # the </ul> must close before the paragraph starts
    assert html.index('</ul>') < html.index('<p')


def test_md_to_html_mixed_paragraphs_and_lists():
    html = md_to_html("Intro line.\n- a\n- b\nOutro line.")
    assert html.count('<ul') == 1
    assert html.count('</ul>') == 1


# --- parse_feedback ---

SAMPLE_FEEDBACK = """## Overall Impression
You have a solid CV.

## Strengths
- **Clear structure**: Easy to scan.

## Areas for Improvement

**1. Vague bullets**
- **Problem:** Too generic.
- **Fix:** Add metrics.

## Quick Win
Add numbers to your achievements.
"""


def test_parse_feedback_returns_sections_in_order():
    sections = parse_feedback(SAMPLE_FEEDBACK)
    titles = [s[0] for s in sections]
    assert titles == ["Overall Impression", "Strengths", "Areas for Improvement", "Quick Win"]


def test_parse_feedback_maps_known_headers_to_configured_colors():
    sections = parse_feedback(SAMPLE_FEEDBACK)
    by_title = {s[0]: (s[1], s[2]) for s in sections}
    expected_bg, expected_accent = SECTION_CONFIG["strengths"][1], SECTION_CONFIG["strengths"][2]
    assert by_title["Strengths"] == (expected_bg, expected_accent)


def test_parse_feedback_unknown_header_falls_back_to_default_style():
    sections = parse_feedback("## Something Unexpected\nbody text")
    display_title, bg, accent, body = sections[0]
    assert display_title == "Something Unexpected"
    assert bg == "#1a1a1a"
    assert accent == "#888"
    assert body == "body text"


def test_parse_feedback_body_preserved_for_each_section():
    sections = parse_feedback(SAMPLE_FEEDBACK)
    body_by_title = {s[0]: s[3] for s in sections}
    assert "Add numbers to your achievements." in body_by_title["Quick Win"]


# --- extract_text_from_docx ---

def test_extract_text_from_docx_cv1_contains_expected_content():
    text = extract_text_from_docx(load_fixture("CV-1.docx"))
    assert text.strip() != ""


def test_extract_text_from_docx_urdu_mixed_language_cv():
    text = extract_text_from_docx(load_fixture("test_urdu_cv.docx"))
    assert text.strip() != ""


# --- build_error_message ---

@pytest.mark.parametrize("err", ["429 Too Many Requests", "RESOURCE_EXHAUSTED: quota"])
def test_build_error_message_rate_limit(err):
    assert build_error_message(err) == (
        "RedPen is getting a lot of traffic right now. Please try again in a minute."
    )


@pytest.mark.parametrize("err", ["401 Unauthorized", "403 Forbidden", "permission denied", "unauthenticated"])
def test_build_error_message_auth_failure(err):
    assert build_error_message(err) == "Something went wrong on our end. Please try again shortly."


def test_build_error_message_generic_fallback():
    assert build_error_message("connection reset by peer") == "Something went wrong. Please try again."
