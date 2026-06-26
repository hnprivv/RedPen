import streamlit as st
from google import genai
from google.genai import types
from docx import Document
import tempfile
import os
import io
import re

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
</style>
""", unsafe_allow_html=True)

# --- Prompts ---

PROMPT_CV_ONLY = """You are an expert CV reviewer with 15 years of experience in recruitment across tech, finance, and consulting.
You review CVs with sharp, specific feedback, you never give vague advice.

You will always return your review in EXACTLY this structure, with EXACTLY these section headers.
Never deviate from this format regardless of CV language or content:

## Overall Impression
[2-3 sentences giving a candid, holistic view of the CV's current state and the impression it makes on a recruiter in the first 10 seconds.]

## Strengths
- **[Strength title]**: [One specific sentence explaining what works and why, with reference to actual content from the CV.]
- **[Strength title]**: [One specific sentence.]

## Areas for Improvement

**1. [Issue title]**
- **Problem:** [One sentence describing the specific issue, referencing actual content from the CV.]
- **Fix:** [A concrete rewrite example or a specific action — not generic advice.]

**2. [Issue title]**
- **Problem:** [...]
- **Fix:** [...]

**3. [Issue title]**
- **Problem:** [...]
- **Fix:** [...]

## Quick Win
[One single change — the highest-impact edit they could make in the next 10 minutes. Be direct and specific.]

Rules you must follow:
- Reference actual content from the CV (job titles, company names, specific phrases). Never give feedback that could apply to any CV.
- "Fix" examples must be concrete rewrites or specific actions, not suggestions like "add more detail."
- If the CV mixes languages (e.g. Urdu and English), review it fully — do not flag the language mix as a problem unless it genuinely hurts clarity.
- Keep the total response under 450 words.
"""

PROMPT_CV_WITH_JD = """You are an expert CV reviewer and recruitment specialist with 15 years of experience across tech, finance, and consulting.
You are given a CV and a job description. Your job is to assess how well the candidate is positioned for this specific role.

You will always return your review in EXACTLY this structure, with EXACTLY these section headers.
Never deviate from this format regardless of CV language or content:

## Overall Impression
[2-3 sentences on the candidate's overall profile and the immediate impression their CV makes for this specific role.]

## Strengths
- **[Strength title]**: [One specific sentence on what in the CV aligns well with this role, referencing actual content from both.]
- **[Strength title]**: [One specific sentence.]

## Job Fit
[2-3 sentences assessing how well the CV matches the job description overall — what aligns, what's weak, and whether the candidate would clear an initial screen.]

## Gaps

**1. [Gap title]**
- **Missing:** [What the job description requires that is absent or underrepresented in the CV.]
- **Fix:** [Concrete action — reword an existing bullet, add a specific example, or surface a skill that's implied but not stated.]

**2. [Gap title]**
- **Missing:** [...]
- **Fix:** [...]

**3. [Gap title]**
- **Missing:** [...]
- **Fix:** [...]

## Areas for Improvement

**1. [Issue title]**
- **Problem:** [A general CV quality issue unrelated to the role — formatting, vague language, missing metrics, etc.]
- **Fix:** [Concrete rewrite or specific action.]

**2. [Issue title]**
- **Problem:** [...]
- **Fix:** [...]

## Quick Win
[The single change that would most improve this CV's chances for this specific role. Be direct and specific.]

Rules you must follow:
- Always tie Gaps feedback to specific content in both the CV and the job description.
- Areas for Improvement should be role-agnostic CV quality issues.
- "Fix" examples must be concrete rewrites or specific actions, not suggestions like "add more detail."
- If the CV mixes languages (e.g. Urdu and English), review it fully — do not flag the language mix as a problem unless it genuinely hurts clarity.
- Keep the total response under 600 words.
"""

# --- Section card config ---

SECTION_CONFIG = {
    "overall impression": ("🔍 Overall Impression", "#0d1b2a", "#4a9eff"),
    "strengths":          ("✅ Strengths",           "#0a1f12", "#43a047"),
    "job fit":            ("🎯 Job Fit",             "#0d1b2a", "#2196f3"),
    "gaps":               ("⚠️ Gaps",               "#1f1500", "#ffa726"),
    "areas for improvement": ("🔧 Areas for Improvement", "#1f1200", "#ef6c00"),
    "quick win":          ("⚡ Quick Win",           "#160b2e", "#ab47bc"),
}

def md_to_html(text: str) -> str:
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    lines = text.strip().split('\n')
    html, in_ul = [], False
    for line in lines:
        s = line.strip()
        if not s:
            if in_ul:
                html.append('</ul>')
                in_ul = False
            continue
        if s.startswith('- '):
            if not in_ul:
                html.append('<ul style="padding-left:1.2rem;margin:0.5rem 0;">')
                in_ul = True
            html.append(f'<li style="margin-bottom:0.5rem;">{s[2:]}</li>')
        else:
            if in_ul:
                html.append('</ul>')
                in_ul = False
            html.append(f'<p style="margin:0.4rem 0;">{s}</p>')
    if in_ul:
        html.append('</ul>')
    return '\n'.join(html)

def render_feedback(feedback: str):
    parts = re.split(r'\n?## ', feedback.strip())
    index = 0
    for part in parts:
        if not part.strip():
            continue
        lines = part.strip().split('\n', 1)
        header_raw = lines[0].strip().lstrip('#').strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        key = header_raw.lower()
        display_title, bg, accent = SECTION_CONFIG.get(key, (header_raw, "#1a1a1a", "#888"))
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
        index += 1

# --- Extraction ---

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    texts = [
        elem.text
        for elem in doc.element.body.iter(f"{{{W}}}t")
        if elem.text
    ]
    return " ".join(texts)

# --- Gemini ---

def review_cv(file_bytes: bytes, ext: str, api_key: str, job_description: str) -> str:
    client = genai.Client(api_key=api_key)
    has_jd = bool(job_description.strip())
    system_prompt = PROMPT_CV_WITH_JD if has_jd else PROMPT_CV_ONLY

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


if run:
    if not uploaded_file:
        with left_col:
            st.warning("Please upload a CV first.")
        st.stop()

    file_bytes = uploaded_file.read()
    ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        with left_col:
            st.error("GEMINI_API_KEY not found. Add it to .streamlit/secrets.toml.")
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
        status_placeholder.empty()
        with left_col:
            st.error(f"Review failed: {e}")
        st.stop()

    status_placeholder.empty()

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
