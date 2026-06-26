# RedPen

An AI-powered CV reviewer built with Streamlit and Google Gemini. Upload a CV and get structured, specific feedback in seconds, not a wall of generic suggestions, but actionable critique tied to actual content in your document.

Optionally paste a job description to switch into gap analysis mode, where the tool compares your CV against the role and tells you exactly what's missing and how to fix it.

## What it does

**CV-only mode** reviews four things:
- Overall impression — the honest first read a recruiter gets in 10 seconds
- Strengths — what's working and why, with reference to actual content
- Areas for improvement — specific problems with concrete rewrites, not vague advice
- Quick win — the single highest-impact change to make right now

**CV + Job Description mode** adds:
- Job fit — how well the CV positions the candidate for this specific role
- Gaps — what the Job Description asks for that the CV doesn't show, with fixes tied to both documents

The output format is locked - same sections, same structure, every time. The content varies per CV, the structure never does.

## Why it works on design-tool PDFs

Most CV reviewers break on PDFs exported from Canva or similar tools because the text is rendered as vector paths, not actual characters. This tool sends PDFs directly to Gemini's vision API instead of extracting text first, so it reads the document the same way a human would — visually. DOCX files use raw XML extraction to catch content in text boxes and shapes that standard paragraph parsing misses.

## Tech stack

- **Streamlit** — UI and deployment
- **Google Gemini 3.1 Flash Lite** — feedback generation
- **python-docx** — DOCX text extraction via raw XML
- **google-genai** — Gemini API client

## Running locally

```bash
git clone https://github.com/hnprivv/RedPen
cd RedPen
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

Add your Gemini API key to `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your-key-here"
```

Get a free key at [aistudio.google.com](https://aistudio.google.com).

```bash
streamlit run app.py
```

## Deploying to Streamlit Cloud

1. Push the repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo
3. Set main file to `app.py`
4. Under Advanced settings → Secrets, add your `GEMINI_API_KEY`
5. Deploy

---

Built by [Huzaifa Najam](https://github.com/hnprivv).