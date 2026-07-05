import streamlit as st
from google import genai
from google.genai import types
import tempfile
import os

from core import (
    select_prompt,
    md_to_html,
    parse_feedback,
    extract_text_from_docx,
    build_error_message,
)

st.set_page_config(
    page_title="RedPen",
    page_icon="icon.png",
    layout="wide",
)

st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }

html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

.card-body p, .card-body li {
    text-align: justify;
}

[data-testid="stFileUploader"] {
    border: 2px dashed #2e2e2e;
    border-radius: 12px;
    padding: 0.5rem;
    background: #0f0f0f;
}

textarea {
    background: #0f0f0f !important;
    border: 1px solid #2e2e2e !important;
    border-radius: 10px !important;
    color: #e0e0e0 !important;
    font-size: 0.9rem !important;
}

div[data-testid="stButton"] > button {
    width: 100%;
    background: #1a56db;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.65rem 1rem;
    font-size: 1rem;
    font-weight: 700;
    cursor: pointer;
    margin-top: 0.5rem;
    transition: background 0.2s;
}
div[data-testid="stButton"] > button:hover {
    background: #1446c0;
    color: white;
    border: none;
}

.cv-spinner {
    width: 18px;
    height: 18px;
    border: 2px solid #1a56db40;
    border-top-color: #1a56db;
    border-radius: 50%;
    animation: cv-spin 0.8s linear infinite;
    display: inline-block;
}
@keyframes cv-spin {
    to { transform: rotate(360deg); }
}


hr { border-color: #2e2e2e; }

@keyframes cardEnter {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0); }
}

[data-testid="stHorizontalBlock"] {
    align-items: flex-start;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
    position: sticky;
    top: 2rem;
}
@media (max-width: 768px) {
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
        position: static;
    }
}
</style>
""", unsafe_allow_html=True)

def render_feedback(feedback: str):
    sections = parse_feedback(feedback)
    for index, (display_title, bg, accent, body) in enumerate(sections):
        body_html = md_to_html(body)
        delay = index * 0.12
        st.markdown(f"""
        <div style="background:{bg}; border-left:4px solid {accent}; border-radius:10px;
                    padding:1.25rem 1.5rem; margin-bottom:1rem; color:#e0e0e0;
                    opacity:0; animation:cardEnter 0.4s ease forwards;
                    animation-delay:{delay}s;">
            <div style="color:{accent}; font-weight:700; font-size:1rem;
                        margin-bottom:0.75rem; letter-spacing:0.01em;">
                {display_title}
            </div>
            <div class="card-body">
                {body_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- Gemini ---

def review_cv(file_bytes: bytes, ext: str, api_key: str, job_description: str) -> str:
    client = genai.Client(api_key=api_key)
    has_jd = bool(job_description.strip())
    system_prompt = select_prompt(job_description)

    if ext == "pdf":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        try:
            uploaded = client.files.upload(file=tmp_path)
            if has_jd:
                contents = [uploaded, f"Job Description:\n{job_description}\n\nPlease review this CV against the job description."]
            else:
                contents = [uploaded, "Please review this CV."]
        finally:
            os.unlink(tmp_path)
    else:
        cv_text = extract_text_from_docx(file_bytes)
        if not cv_text.strip():
            st.error("Could not extract text from this DOCX file.")
            st.stop()
        if has_jd:
            contents = f"Job Description:\n{job_description}\n\nCV:\n{cv_text}\n\nPlease review this CV against the job description."
        else:
            contents = f"Please review this CV:\n\n{cv_text}"

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

# --- UI ---

if "feedback" not in st.session_state:
    st.session_state.feedback = None

left_col, right_col = st.columns([1, 1.4], gap="large")

with left_col:
    st.markdown("""
    <div style="padding:2.5rem 0 2rem;">
        <div style="font-size:2.6rem; font-weight:800; letter-spacing:-0.02em; margin-bottom:0.5rem;">
            Welcome to RedPen
        </div>
        <div style="color:#888; font-size:1rem; line-height:1.6;">
            Upload your CV and get sharp, structured feedback in seconds.<br>
            Paste a job description to unlock a role-specific gap analysis.
        </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload your CV — PDF or Word",
        type=["pdf", "docx"],
    )

    if not uploaded_file:
        st.session_state.feedback = None

    job_description = st.text_area(
        "Job Description (optional)",
        placeholder="Paste the job description for a role you're applying to, and we'll analyze how well your CV fits.",
        height=150,
    )

    run = st.button("Submit")
    status_placeholder = st.empty()

right_placeholder = right_col.empty()

if st.session_state.feedback:
    with right_placeholder.container():
        render_feedback(st.session_state.feedback)
else:
    right_placeholder.markdown("""
    <div style="border:2px dashed #2e2e2e; border-radius:12px;
                height:500px; display:flex; flex-direction:column;
                align-items:center; justify-content:center; gap:0.75rem;
                margin-top:2.5rem;">
        <div style="font-size:1.5rem;">📋</div>
        <div style="color:#444; font-size:0.95rem; font-weight:500;">
            Your feedback will appear here.
        </div>
        <div style="color:#333; font-size:0.82rem;">
            Upload a CV and click Submit to get started.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="margin-top:2rem; padding:1rem 0; border-top:1px solid #6f6f6f; text-align:center;">
    <div style="color:#6f6f6f; font-size:0.78rem;">
        © 2026 RedPen by Huzaifa Najam. All rights reserved.
    </div>
    <div style="color:#6f6f6f; font-size:0.73rem; margin-top:0.3rem; line-height:1.5;">
        Your CV is sent to Google Gemini for processing and is not stored.
        Do not upload documents containing sensitive personal data beyond standard CV content.
    </div>
</div>
""", unsafe_allow_html=True)

if run:
    if not uploaded_file:
        status_placeholder.warning("Please upload a CV first.")
        st.stop()

    file_bytes = uploaded_file.read()
    ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        status_placeholder.error("GEMINI_API_KEY not found. Add it to .streamlit/secrets.toml.")
        st.stop()

    status_placeholder.markdown("""
    <div style="display:flex;align-items:center;gap:0.75rem;
                background:#0d1b2a;border:1px solid #1a56db;border-radius:10px;
                padding:0.75rem 1.25rem;margin-top:0.5rem;">
        <div class="cv-spinner"></div>
        <span style="color:#a0b8d8;font-size:0.92rem;font-weight:500;">
            Reviewing your CV — this takes a few seconds...
        </span>
    </div>
    """, unsafe_allow_html=True)

    try:
        st.session_state.feedback = review_cv(file_bytes, ext, api_key, job_description)
    except Exception as e:
        msg = build_error_message(str(e))
        status_placeholder.error(msg)
        st.stop()

    status_placeholder.empty()
    with right_placeholder.container():
        render_feedback(st.session_state.feedback)
