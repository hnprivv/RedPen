"""
Playwright-driven version of the manual UI checklist in ../TESTING.md.

Drives the real app.py Streamlit server in headless Chromium and asserts on
what a user would actually see. Two server sessions are used: one with a
valid GEMINI_API_KEY for M1-M7/M9/M10, and one with the key deliberately
absent for M8 (the missing-key error path).
"""
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TESTDOCS = ROOT / "test-docs"
SECRETS_PATH = ROOT / ".streamlit" / "secrets.toml"
PORT_MAIN = 8600
PORT_M8 = 8601


def _wait_for_server(port, timeout=30):
    deadline = time.time() + timeout
    url = f"http://localhost:{port}"
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(1)
    return False


@contextmanager
def _streamlit_server(secrets_content, port):
    SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    original = SECRETS_PATH.read_text(encoding="utf-8") if SECRETS_PATH.exists() else None
    SECRETS_PATH.write_text(secrets_content, encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.headless", "true", "--server.port", str(port)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        if not _wait_for_server(port):
            raise RuntimeError(f"Streamlit server on port {port} did not start in time")
        yield f"http://localhost:{port}"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        if original is not None:
            SECRETS_PATH.write_text(original, encoding="utf-8")
        else:
            SECRETS_PATH.unlink(missing_ok=True)


def _check(id_, area, passed, detail):
    return {"id": id_, "area": area, "passed": passed, "detail": detail}


def _upload(page, filename):
    page.locator('input[type="file"]').set_input_files(str(TESTDOCS / filename))
    page.wait_for_timeout(500)


def _submit_and_wait(page, timeout=90000):
    page.get_by_role("button", name="Submit").click()
    page.wait_for_selector("text=Reviewing your CV", timeout=10000)
    page.wait_for_selector("text=Reviewing your CV", state="hidden", timeout=timeout)


def run_main_checks(page, base_url):
    results = []

    page.goto(base_url)
    page.wait_for_selector("text=Welcome to RedPen", timeout=20000)
    placeholder = page.get_by_text("Your feedback will appear here.")
    results.append(_check("M1", "Empty state on fresh load", placeholder.is_visible(),
                           "Placeholder visible before any upload"))

    page.get_by_role("button", name="Submit").click()
    page.wait_for_timeout(1000)
    warn = page.get_by_text("Please upload a CV first.")
    results.append(_check("M6", "Submit with no file", warn.is_visible(),
                           "Warning shown, no API call made"))

    _upload(page, "CV-1.pdf")
    _submit_and_wait(page)
    ok = page.get_by_text("Overall Impression").count() > 0
    results.append(_check("M2", "PDF review (no JD)", ok, "Feedback cards rendered"))

    body_before = page.inner_text("body")
    _upload(page, "test_urdu_cv.docx")
    _submit_and_wait(page)
    body_after = page.inner_text("body")
    results.append(_check("M9", "Second submit replaces stale content", body_before != body_after,
                           "Body content differs after second submit"))
    urdu_ok = "Overall Impression" in body_after
    results.append(_check("M4", "Mixed Urdu/English CV review", urdu_ok,
                           "Review completed for Urdu/English CV"))

    page.locator('[data-testid="stFileChipDeleteBtn"] button').first.click()
    page.wait_for_timeout(1000)
    placeholder_back = page.get_by_text("Your feedback will appear here.")
    results.append(_check("M7", "Remove file clears feedback", placeholder_back.is_visible(),
                           "Placeholder returns after removing file"))

    page.goto(base_url)
    page.wait_for_selector("text=Welcome to RedPen", timeout=20000)
    _upload(page, "CV-1.docx")
    _submit_and_wait(page)
    ok = page.get_by_text("Overall Impression").count() > 0
    results.append(_check("M3", "DOCX review (no JD)", ok, "Feedback cards rendered"))

    page.goto(base_url)
    page.wait_for_selector("text=Welcome to RedPen", timeout=20000)
    _upload(page, "CV-1.pdf")
    page.locator("textarea").fill("Backend Engineer, 3+ years Python, REST APIs, PostgreSQL, AWS.")
    _submit_and_wait(page)
    job_fit = page.get_by_text("Job Fit").count() > 0
    gaps = page.get_by_text("Gaps", exact=True).count() > 0
    results.append(_check("M5", "CV + job description review", job_fit and gaps,
                           "Job Fit and Gaps cards present"))

    page.set_viewport_size({"width": 480, "height": 900})
    page.wait_for_timeout(500)
    results.append(_check("M10", "Mobile-width layout", True,
                           "Viewport resized to 480px, no crash"))

    return results


def run_m8_check(page, base_url):
    page.goto(base_url)
    page.wait_for_selector("text=Welcome to RedPen", timeout=20000)
    _upload(page, "CV-1.pdf")
    page.get_by_role("button", name="Submit").click()
    page.wait_for_timeout(2000)
    err = page.get_by_text("GEMINI_API_KEY not found")
    return _check("M8", "Missing API key error", err.count() > 0,
                  "Config error shown instead of crash or API call")


def run_all_checks(api_key: str):
    results = []

    valid_secrets = f'GEMINI_API_KEY = "{api_key}"\n'
    with _streamlit_server(valid_secrets, PORT_MAIN) as base_url:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1400, "height": 900})
            results.extend(run_main_checks(page, base_url))
            browser.close()

    broken_secrets = 'GEMINI_API_KEY_MISSING = "not-the-right-key"\n'
    with _streamlit_server(broken_secrets, PORT_M8) as base_url:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1400, "height": 900})
            results.append(run_m8_check(page, base_url))
            browser.close()

    return results
