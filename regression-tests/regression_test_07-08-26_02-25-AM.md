# Regression Test Report — 2026-07-08 02:25 PKT

**Generated:** 2026-07-08T02:25:42.354321+05:00

See [TESTING.md](../TESTING.md) for what each ID below actually verifies.

## 1. Fast suite (core.py logic)

Command: `pytest -q`

Result: **PASS** — 19 passed, 3 deselected in 1.29s

<details><summary>Full output</summary>

```
...................                                                      [100%]
19 passed, 3 deselected in 1.29s
```
</details>

## 2. Live suite (Gemini prompt contract)

Command: `pytest -m live -q`

Result: **PASS** — 3 passed, 19 deselected in 9.76s

<details><summary>Full output</summary>

```
...                                                                      [100%]
3 passed, 19 deselected in 9.76s
```
</details>

## 3. Manual UI checklist (Playwright-driven)

| ID | Check | Result | Detail |
|----|-------|--------|--------|
| M1 | Empty state on fresh load | PASS | Placeholder visible before any upload |
| M6 | Submit with no file | PASS | Warning shown, no API call made |
| M2 | PDF review (no JD) | PASS | Feedback cards rendered |
| M9 | Second submit replaces stale content | PASS | Body content differs after second submit |
| M4 | Mixed Urdu/English CV review | PASS | Review completed for Urdu/English CV |
| M7 | Remove file clears feedback | PASS | Placeholder returns after removing file |
| M3 | DOCX review (no JD) | PASS | Feedback cards rendered |
| M5 | CV + job description review | PASS | Job Fit and Gaps cards present |
| M10 | Mobile-width layout | PASS | Viewport resized to 480px, no crash |
| M8 | Missing API key error | PASS | Config error shown instead of crash or API call |

## Summary

All checks passed.
