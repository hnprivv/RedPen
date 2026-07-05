#!/usr/bin/env python3
"""
Orchestrates a full regression pass: fast suite, live suite, and the
Playwright-driven manual UI checklist. Writes a dated Markdown report into
this directory. See README.md for usage.
"""
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGRESSION_DIR = Path(__file__).resolve().parent
PKT = timezone(timedelta(hours=5))  # Pakistan Standard Time, no DST


def _run_pytest(args):
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *args],
        cwd=ROOT, capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _summary_line(output: str) -> str:
    lines = [l for l in output.splitlines() if re.search(r"\d+ (passed|failed|error)", l)]
    return lines[-1].strip() if lines else "(no summary line found)"


def run_fast_suite():
    code, output = _run_pytest(["-q"])
    return {
        "name": "Fast suite",
        "command": "pytest -q",
        "passed": code == 0,
        "summary": _summary_line(output),
        "output": output,
    }


def run_live_suite():
    if not os.environ.get("GEMINI_API_KEY"):
        return {
            "name": "Live suite",
            "command": "pytest -m live -q",
            "passed": None,
            "summary": "skipped — GEMINI_API_KEY not set",
            "output": "",
        }
    code, output = _run_pytest(["-m", "live", "-q"])
    return {
        "name": "Live suite",
        "command": "pytest -m live -q",
        "passed": code == 0,
        "summary": _summary_line(output),
        "output": output,
    }


def run_manual_checklist():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return [{
            "id": "M1-M10", "area": "Manual UI checklist", "passed": None,
            "detail": "skipped — GEMINI_API_KEY not set",
        }]
    from checklist import run_all_checks
    return run_all_checks(api_key)


def main():
    fast = run_fast_suite()
    live = run_live_suite()
    manual = run_manual_checklist()

    from report import render_report
    report_md = render_report(fast, live, manual)

    now = datetime.now(PKT)
    filename = now.strftime("regression_test_%m-%d-%y_%I-%M-%p.md")
    out_path = REGRESSION_DIR / filename
    out_path.write_text(report_md, encoding="utf-8")
    print(f"Wrote {out_path}")

    ok = (
        fast["passed"]
        and live["passed"] is not False
        and all(m.get("passed") is not False for m in manual)
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
