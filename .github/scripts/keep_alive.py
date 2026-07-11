"""
Visits the deployed RedPen app with a real browser session so Streamlit
Community Cloud registers it as activity and doesn't hibernate it. A plain
HTTP GET (e.g. curl) isn't enough -- Streamlit Cloud's wake-up flow involves
a cookie-based auth redirect chain and, when the app is asleep, an
interactive "wake up" button that only a real browser session can complete.

Once awake, Streamlit Cloud renders the app's actual content inside a child
iframe (observed at a URL like "<app>/~/+/"), separate from the top-level
page (which is just the Streamlit Cloud viewer chrome -- the sleep/wake
screen, the Fork link, etc.). The readiness check below searches every
frame, not just the top-level page, since the ready text lives in that
iframe once the app has loaded.
"""
import re
import sys
import time

from playwright.sync_api import sync_playwright

URL = "https://redpen-by-hn.streamlit.app/"
WAKE_BUTTON_PATTERN = re.compile(r"wake|get this app back up|yes, get", re.I)
READY_TEXT = "Welcome to RedPen"
READY_TIMEOUT_MS = 240000
POLL_INTERVAL_MS = 5000


def wait_for_app_ready(page, ready_text, timeout_ms, poll_interval_ms):
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        for frame in page.frames:
            try:
                if ready_text in frame.inner_text("body"):
                    print(f"App ready -- found '{ready_text}' in frame: {frame.url}")
                    return True
            except Exception:
                continue
        page.wait_for_timeout(poll_interval_ms)
    return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL, wait_until="load", timeout=60000)

        wake_button = page.get_by_role("button", name=WAKE_BUTTON_PATTERN)
        try:
            wake_button.first.click(timeout=15000)
            print("App appears asleep -- clicked wake-up button.")
        except Exception:
            print("No wake-up button found within 15s; app may already be awake.")

        if not wait_for_app_ready(page, READY_TEXT, READY_TIMEOUT_MS, POLL_INTERVAL_MS):
            print(f"App did not load within {READY_TIMEOUT_MS // 1000}s (checked all frames).")
            browser.close()
            sys.exit(1)

        print("App is awake and loaded successfully.")
        browser.close()


if __name__ == "__main__":
    main()
