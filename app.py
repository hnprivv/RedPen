import streamlit as st
from google import genai
from google.genai import types
from docx import Document
import tempfile
import os
import io

st.set_page_config(
    page_title="CV Reviewer",
    page_icon="📄",
    layout="centered",
)

st.markdown(
    """
    <style>
    .block-container p, .block-container li {
        text-align: justify;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    texts = [
        elem.text
        for elem in doc.element.body.iter(f"{{{W}}}t")
        if elem.text
    ]
    return " ".join(texts)

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

st.title("CV Reviewer")
st.caption("Upload your CV and get structured, specific feedback in seconds.")

uploaded_file = st.file_uploader(
    "Upload your CV (PDF or Word)",
    type=["pdf", "docx"],
    label_visibility="collapsed",
)

job_description = st.text_area(
    "Job description (optional)",
    placeholder="Paste the job description here to get a gap analysis against this specific role." \
    "The system will review your CV against this job description and provide feedback on how well you are positioned for this role.",
    height=160,
)

if uploaded_file:
    file_bytes = uploaded_file.read()
    ext = uploaded_file.name.rsplit(".", 1)[-1].lower()

    with st.spinner("Reviewing..."):
        try:
            feedback = review_cv(
                file_bytes, ext,
                st.secrets.get("GEMINI_API_KEY", ""),
                job_description,
            )
        except Exception as e:
            st.error(f"Review failed: {e}")
            st.stop()

    st.divider()
    st.markdown(feedback)
    st.divider()

    st.download_button(
        label="Download Feedback",
        data=feedback,
        file_name="cv_feedback.md",
        mime="text/markdown",
    )
