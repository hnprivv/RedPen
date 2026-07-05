# Regression Tests

This directory holds **evidence**, not source. Every time a commit lands on
`main`, `.github/workflows/regression.yml` runs the full regression pass —
fast suite, live suite, and the Playwright-driven manual UI checklist — and
commits a dated report here.

For what each check actually verifies, see [`../TESTING.md`](../TESTING.md).
This directory is the historical record of runs; `TESTING.md` is the
reference for what the IDs (C1–C15, L1–L3, M1–M10) mean.

## Files

- `run_regression.py` — orchestrator. Runs the fast suite, the live suite,
  and the manual checklist (via `checklist.py`), then writes a report
  (via `report.py`).
- `checklist.py` — drives the actual Streamlit app in headless Chromium
  (Playwright) to exercise M1–M10 exactly as a user would: upload, submit,
  wait for the real Gemini response, and assert on what's rendered.
- `report.py` — renders the collected results into the Markdown report.
- `regression_test_<MM-DD-YY>_<HH-MM>-<AM|PM>.md` — one report per CI run,
  timestamped in PKT (UTC+5, e.g. `regression_test_07-05-26_02-36-PM.md`).

## Running it yourself

Requires `GEMINI_API_KEY` in the environment (the live suite and manual
checklist both make real Gemini API calls — this costs quota and takes
roughly a minute to run end to end).

```
pip install -r requirements-dev.txt
python -m playwright install chromium
```

PowerShell:
```powershell
$env:GEMINI_API_KEY = "your-key-here"
python regression-tests/run_regression.py
```

Bash:
```bash
export GEMINI_API_KEY="your-key-here"
python regression-tests/run_regression.py
```

This writes a new dated report into this directory and prints its path.
Without `GEMINI_API_KEY` set, only the fast suite runs; the live suite and
manual checklist sections are marked skipped in the report.

## CI behavior

- Trigger: push to `main` only (the live suite + manual checklist together
  make roughly a dozen real Gemini API calls per run, so this is
  deliberately not wired to every branch/PR push).
- The workflow writes `.streamlit/secrets.toml` from the `GEMINI_API_KEY`
  repository secret before running — nothing secret is ever committed.
- The generated report is committed straight back to `main` with
  `[skip ci]` in the message, so it doesn't re-trigger the workflow.
- If any check fails, the report is still committed (so failures are
  visible), but the workflow run itself is marked failed.
