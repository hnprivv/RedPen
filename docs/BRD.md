# Business Requirements Document (BRD)

**Project:** RedPen — AI-Powered CV Reviewer
**Author:** Huzaifa Najam
**Status:** Active
**Related documents:** [FSD](FSD.md), [TSD](TSD.md)

---

## 1. Purpose

This document defines the business case, objectives, scope, and requirements for RedPen, an
AI-powered CV review tool. It is the source of truth for *why* RedPen exists and *what* it must
achieve for its users, independent of how it is implemented. The [FSD](FSD.md) translates these
requirements into functional behavior; the [TSD](TSD.md) translates that behavior into technical
design.

## 2. Background

Job seekers routinely rely on generic, one-size-fits-all CV advice (templates, checklists, or
friends/family review) that doesn't reference the actual content of their document and doesn't
account for the specific role they're applying to. Professional CV review services exist but are
slow (days of turnaround) and costly. There is a gap for a tool that gives specific, actionable
feedback tied to a candidate's actual CV content, instantly, and optionally tailored to a target
job description.

## 3. Business Objectives

<table>
<colgroup><col style="width:10%"><col style="width:90%"></colgroup>
<thead><tr><th>ID</th><th>Objective</th></tr></thead>
<tbody>
<tr><td style="white-space:nowrap">BO-1</td><td>Reduce the CV feedback loop from days (human reviewer turnaround) to seconds.</td></tr>
<tr><td style="white-space:nowrap">BO-2</td><td>Deliver feedback that references the candidate's actual content — not generic, templated advice that could apply to any CV.</td></tr>
<tr><td style="white-space:nowrap">BO-3</td><td>Support role-specific gap analysis when a candidate has a target job in mind, not just generic CV quality feedback.</td></tr>
<tr><td style="white-space:nowrap">BO-4</td><td>Handle real-world CV formats and content as submitted by candidates — including design-tool PDF exports and multi-language content — without requiring the candidate to reformat or translate their document first.</td></tr>
<tr><td style="white-space:nowrap">BO-5</td><td>Demonstrate a production-quality engineering process (structured requirements, automated regression testing, CI) suitable as a professional portfolio artifact.</td></tr>
</tbody>
</table>

## 4. Scope

### 4.1 In scope

- Single-document CV upload and review (PDF or DOCX).
- Two review modes: CV-only (general quality feedback) and CV + job description (role-fit gap analysis).
- Structured, consistently-formatted feedback output.
- Web-based delivery, accessible without installation.
- Handling of CVs containing mixed-language content (e.g., Urdu and English).

### 4.2 Out of scope

- User accounts, saved history, or multi-CV comparison.
- Editing or generating a CV on the candidate's behalf (RedPen critiques; it does not rewrite the document itself).
- Applicant tracking system (ATS) integration or bulk/batch processing of multiple candidates.
- Storage or retention of uploaded CVs beyond the processing of a single request.
- Support for CV formats other than PDF and DOCX (e.g., plain text, images, LinkedIn export).

## 5. Stakeholders

| Stakeholder | Interest |
|-------------|----------|
| End user (job seeker) | Wants fast, specific, actionable feedback on their CV, optionally against a target role. |
| Product owner / developer (Huzaifa Najam) | Owns the product and engineering process; uses RedPen as a portfolio demonstration of full-stack AI product delivery. |
| Prospective employer / technical reviewer | Evaluates RedPen as evidence of the owner's ability to scope, build, test, and ship an AI-integrated product. |

## 6. Business Requirements

<table>
<colgroup><col style="width:10%"><col style="width:90%"></colgroup>
<thead><tr><th>ID</th><th>Requirement</th></tr></thead>
<tbody>
<tr><td style="white-space:nowrap">BR-1</td><td>The system shall allow a user to submit a CV without creating an account or providing any identifying information beyond the document itself.</td></tr>
<tr><td style="white-space:nowrap">BR-2</td><td>The system shall accept CVs in the formats most commonly produced by job seekers: PDF and Microsoft Word (DOCX).</td></tr>
<tr><td style="white-space:nowrap">BR-3</td><td>The system shall return feedback that references specific content from the submitted CV (e.g., actual job titles, phrases, achievements) rather than advice generic enough to apply to any document.</td></tr>
<tr><td style="white-space:nowrap">BR-4</td><td>The system shall optionally accept a job description and, when provided, assess the CV specifically against that role rather than only in general terms.</td></tr>
<tr><td style="white-space:nowrap">BR-5</td><td>The system shall return feedback within a timeframe consistent with a single interactive session (target: under 10 seconds; see <a href="FSD.md">FSD</a> for the measured range).</td></tr>
<tr><td style="white-space:nowrap">BR-6</td><td>The system shall not penalize or flag a CV for containing multiple languages unless the language mix itself genuinely harms clarity.</td></tr>
<tr><td style="white-space:nowrap">BR-7</td><td>The system shall present feedback in a consistent, structured format so that the value of a review does not depend on how well the candidate can interpret unstructured prose.</td></tr>
<tr><td style="white-space:nowrap">BR-8</td><td>The system shall inform the user what happens to their document (i.e., that it is sent to a third-party AI provider for processing and is not stored) before or at the point of submission.</td></tr>
<tr><td style="white-space:nowrap">BR-9</td><td>The system's behavior shall be verifiable through automated regression testing so that changes to the product do not silently degrade the quality or structure of feedback delivered to users.</td></tr>
</tbody>
</table>

## 7. Assumptions

- Users have a CV already prepared in PDF or DOCX format; RedPen is a review tool, not an authoring tool.
- Users have access to a modern web browser; no native mobile app is required.
- The underlying AI model (currently Google Gemini) is treated as a swappable dependency — business requirements are defined in terms of the feedback users receive, not the specific model that generates it.
- Reasonable, good-faith use: the system is not designed to defend against adversarial inputs (e.g., prompt injection via CV content) beyond normal operation.

## 8. Constraints

- Single-developer project with no dedicated QA, infra, or support team — operational simplicity is a first-class requirement, not a nice-to-have.
- Dependent on a third-party LLM API (Google Gemini) for its core feedback-generation capability; availability and rate limits of that service are outside RedPen's control.
- Hosted on Streamlit Community Cloud, which constrains scaling, custom infrastructure, and deployment control.

## 9. Success Criteria

| Metric | Target |
|--------|--------|
| Time to feedback | Under 10 seconds from submission to rendered review, for a typical CV. |
| Feedback specificity | Every review references at least one piece of content specific to the submitted CV (job title, company, phrase, or metric). |
| Format coverage | Successfully extracts reviewable content from both PDF (including design-tool exports) and DOCX CVs. |
| Regression coverage | Every core behavior (prompt selection, output structure, format extraction, error handling, and the end-to-end UI flow) has an automated, repeatable test, run on every code change to `main`. |

## 10. Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Third-party model provider changes pricing, availability, or output behavior. | Feedback quality or availability degrades without a code change on RedPen's side. | Prompt/output contract is covered by automated live-API tests ([TESTING.md](../TESTING.md)) that catch structural drift early. |
| Free-tier API rate limits are exceeded under load. | Users see a temporary failure instead of feedback. | Rate-limit errors are caught and shown as a clear, user-facing message rather than a crash. |
| A prompt or UI change silently breaks the feedback structure or a document-format code path. | Users receive malformed or missing feedback without anyone noticing. | Automated regression suite (unit, live-API, and UI layers) runs on every commit to `main` and produces a dated, auditable report. |

## 11. Glossary

| Term | Definition |
|------|-----------|
| CV | Curriculum Vitae — the candidate's resume document submitted for review. |
| JD | Job Description — an optional second input describing a target role, used to tailor feedback. |
| Gap analysis | The comparison of a CV against a job description to identify what the role requires that the CV doesn't demonstrate. |
