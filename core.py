import io
import re

from docx import Document

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
- Always address the user directly using "you" and "your" — never refer to them as "the candidate" or by name.
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
- Always address the user directly using "you" and "your" — never refer to them as "the candidate" or by name.
- Always tie Gaps feedback to specific content in both the CV and the job description.
- Areas for Improvement should be role-agnostic CV quality issues.
- "Fix" examples must be concrete rewrites or specific actions, not suggestions like "add more detail."
- If the CV mixes languages (e.g. Urdu and English), review it fully — do not flag the language mix as a problem unless it genuinely hurts clarity.
- Keep the total response under 600 words.
"""

# --- Section card config ---

SECTION_CONFIG = {
    "overall impression": ("Overall Impression", "#0d1b2a", "#4a9eff"),
    "strengths":          ("Strengths",           "#0a1f12", "#43a047"),
    "job fit":            ("Job Fit",             "#0d1b2a", "#2196f3"),
    "gaps":               ("Gaps",               "#1f0a0a", "#e53935"),
    "areas for improvement": ("Areas for Improvement", "#1f1200", "#ef6c00"),
    "quick win":          ("Quick Win",           "#160b2e", "#ab47bc"),
}


def select_prompt(job_description: str) -> str:
    return PROMPT_CV_WITH_JD if job_description.strip() else PROMPT_CV_ONLY


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


def parse_feedback(feedback: str):
    """Split a feedback response into ordered (display_title, bg, accent, body) sections."""
    parts = re.split(r'\n?## ', feedback.strip())
    sections = []
    for part in parts:
        if not part.strip():
            continue
        lines = part.strip().split('\n', 1)
        header_raw = lines[0].strip().lstrip('#').strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        key = header_raw.lower()
        display_title, bg, accent = SECTION_CONFIG.get(key, (header_raw, "#1a1a1a", "#888"))
        sections.append((display_title, bg, accent, body))
    return sections


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    texts = [
        elem.text
        for elem in doc.element.body.iter(f"{{{W}}}t")
        if elem.text
    ]
    return " ".join(texts)


def build_error_message(err: str) -> str:
    if "429" in err or "resource_exhausted" in err.lower():
        return "RedPen is getting a lot of traffic right now. Please try again in a minute."
    if any(x in err for x in ["401", "403", "unauthenticated", "permission"]):
        return "Something went wrong on our end. Please try again shortly."
    return "Something went wrong. Please try again."
