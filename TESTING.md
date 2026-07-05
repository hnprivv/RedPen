# RedPen — Regression Testing

RedPen has three layers, each tested differently:

1. **Pure logic** (`core.py`) — prompt selection, feedback parsing, markdown-to-HTML, DOCX
   extraction, error-message mapping. Covered by fast, deterministic pytest tests. No network
   calls, no Streamlit runtime needed.
2. **Prompt/LLM contract** — the exact structure Gemini must return for `app.py`'s
   `render_feedback` to render correctly (section headers, word-count ceilings). Covered by
   pytest tests marked `live`, which hit the real Gemini API and are excluded from the default run.
3. **Streamlit UI flow** — file upload, button, spinner, error banners, card rendering. Covered by
   a manual checklist (no automated UI test framework in this project).

## Setup

```
pip install -r requirements-dev.txt
```

## Running tests

```
pytest              # fast suite only (core.py) — run this before every commit
pytest -m live       # prompt/LLM structural checks — needs GEMINI_API_KEY env var, costs quota
```

Run `pytest -m live` whenever `PROMPT_CV_ONLY`, `PROMPT_CV_WITH_JD`, `SECTION_CONFIG`, the model
name, or `temperature`/`max_output_tokens` change — those are the only things that can silently
break the mapping between Gemini's output and the rendered cards.

## Automated test cases (`tests/test_core.py`)

| ID | Area | Case | Expected |
|----|------|------|----------|
| C1 | `select_prompt` | no job description | returns `PROMPT_CV_ONLY` |
| C2 | `select_prompt` | job description given | returns `PROMPT_CV_WITH_JD` |
| C3 | `md_to_html` | `**bold**` text | wrapped in `<strong>` |
| C4 | `md_to_html` | `- ` bullet lines | wrapped in a single `<ul>`/`</ul>` |
| C5 | `md_to_html` | blank line after a list | list closes before next paragraph |
| C6 | `md_to_html` | paragraph, list, paragraph | exactly one `<ul>`/`</ul>` pair |
| C7 | `parse_feedback` | full sample response | sections returned in original order |
| C8 | `parse_feedback` | known header (e.g. "Strengths") | mapped to its `SECTION_CONFIG` colors |
| C9 | `parse_feedback` | unrecognized header | falls back to default gray card, header preserved |
| C10 | `parse_feedback` | any section | body text preserved verbatim |
| C11 | `extract_text_from_docx` | `test-docs/CV-1.docx` | non-empty extracted text |
| C12 | `extract_text_from_docx` | `test-docs/test_urdu_cv.docx` (mixed Urdu/English) | non-empty extracted text |
| C13 | `build_error_message` | `"429"` / `"resource_exhausted"` in error | rate-limit message |
| C14 | `build_error_message` | `"401"` / `"403"` / `"unauthenticated"` / `"permission"` in error | generic "our end" message |
| C15 | `build_error_message` | anything else | generic fallback message |

## Prompt/LLM contract test cases (`tests/test_prompts_live.py`, `-m live`)

| ID | Area | Case | Expected |
|----|------|------|----------|
| L1 | CV-only prompt | fixture CV, no JD | response contains `## Overall Impression`, `## Strengths`, `## Areas for Improvement`, `## Quick Win`, in that order; ≤ ~450 words |
| L2 | CV+JD prompt | fixture CV + sample JD | response contains all six expected headers; ≤ ~600 words |
| L3 | CV-only prompt | fixture CV | response never says "the candidate" (must address the user directly) |

## Manual UI checklist (`app.py`)

Run this pass before any release, and whenever `app.py`'s UI code changes.

| ID | Steps | Expected |
|----|-------|----------|
| M1 | Load the app fresh | Empty state placeholder shown on the right; no feedback cards |
| M2 | Upload `test-docs/CV-1.pdf`, no JD, click Submit | Spinner shows, then feedback cards render with CV-only structure |
| M3 | Upload `test-docs/CV-1.docx`, no JD, click Submit | Same as M2 (DOCX path) |
| M4 | Upload `test-docs/test_urdu_cv.docx`, no JD, click Submit | Review completes; mixed-language content is not flagged as a problem |
| M5 | Upload a CV + paste a job description, click Submit | Feedback includes Job Fit and Gaps cards |
| M6 | Click Submit with no file uploaded | Warning: "Please upload a CV first." No API call made |
| M7 | Remove the uploaded file after a review has completed | Feedback clears, empty-state placeholder returns |
| M8 | Temporarily rename/remove `GEMINI_API_KEY` in `.streamlit/secrets.toml`, restart, Submit | Error: "GEMINI_API_KEY not found..." |
| M9 | Submit twice in a row | Second run replaces the first; no stale cards left over |
| M10 | Resize window to mobile width | Left column un-sticks (no overlap with right column) |

## Run log

Record every regression pass here — date, commit, pass/fail, notes.

| Date | Commit | Fast suite | Live suite | Manual checklist | Notes |
|------|--------|-----------|-----------|-------------------|-------|
| 2026-07-05 | (pre-`core.py` refactor commit) | 19/19 pass | 3/3 pass | M1–M10 all pass | Extracted pure logic from `app.py` into `core.py`. M1–M7, M9, M10 driven end-to-end with a headless-Chromium Playwright script against the real Gemini API (key already present in `.streamlit/secrets.toml`). All passed, including the mixed Urdu/English CV (M4), which the model reviewed fully without flagging the language mix, and the stale-content check (M9), which required fixing the test itself — the first pass gave a false positive by matching leftover DOM text from the prior review before the new response had arrived; waiting on the spinner's hidden state instead of just the header text fixed it. M8 was verified manually by the user: `GEMINI_API_KEY` in `.streamlit/secrets.toml` was deliberately misspelled to `GEMINI_API_KE`, and the app correctly showed "GEMINI_API_KEY not found. Add it to .streamlit/secrets.toml" rather than crashing or calling the API. Live suite (L1–L3) run by the user via `pytest -m live` with `GEMINI_API_KEY` set as an env var; first attempt failed with `API key not valid` because the env var held only 13 of the real 53 characters (truncated/mis-set in a different shell), not an actual key or code problem — re-setting it correctly in the same session fixed it, all 3 passed. |
