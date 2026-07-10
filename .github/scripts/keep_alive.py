"""
Visits the deployed RedPen app with a real browser session so Streamlit
Community Cloud registers it as activity and doesn't hibernate it. A plain
HTTP GET (e.g. curl) isn't enough -- Streamlit Cloud's wake-up flow involves
a cookie-based auth redirect chain and, when the app is asleep, an
interactive "wake up" button that only a real browser session can complete.
"""
import re
import sys

from playwright.sync_api import sync_playwright

URL = "https://redpen-by-hn.streamlit.app/"
WAKE_BUTTON_PATTERN = re.compile(r"wake|get this app back up|yes, get", re.I)
READY_TEXT = "Welcome to RedPen"


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

        try:
            page.wait_for_selector(f"text={READY_TEXT}", timeout=240000)
        except Exception as e:
            print(f"App did not load within timeout: {e}")
            browser.close()
            sys.exit(1)

        print("App is awake and loaded successfully.")
        browser.close()


if __name__ == "__main__":
    main()
