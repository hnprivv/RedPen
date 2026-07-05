from datetime import datetime, timedelta, timezone

PKT = timezone(timedelta(hours=5))  # Pakistan Standard Time, no DST


def _status_icon(passed):
    if passed is True:
        return "PASS"
    if passed is False:
        return "FAIL"
    return "SKIPPED"


def _pytest_section(title, result):
    lines = [
        f"## {title}",
        "",
        f"Command: `{result['command']}`",
        "",
        f"Result: **{_status_icon(result['passed'])}** — {result['summary']}",
        "",
    ]
    if result["output"]:
        lines += [
            "<details><summary>Full output</summary>",
            "",
            "```",
            result["output"].rstrip(),
            "```",
            "</details>",
            "",
        ]
    return "\n".join(lines)


def render_report(fast: dict, live: dict, manual: list) -> str:
    now = datetime.now(PKT)
    lines = [
        f"# Regression Test Report — {now.strftime('%Y-%m-%d %H:%M PKT')}",
        "",
        f"**Generated:** {now.isoformat()}",
        "",
        "See [TESTING.md](../TESTING.md) for what each ID below actually verifies.",
        "",
        _pytest_section("1. Fast suite (core.py logic)", fast),
        _pytest_section("2. Live suite (Gemini prompt contract)", live),
        "## 3. Manual UI checklist (Playwright-driven)",
        "",
        "| ID | Check | Result | Detail |",
        "|----|-------|--------|--------|",
    ]
    for m in manual:
        lines.append(f"| {m['id']} | {m['area']} | {_status_icon(m['passed'])} | {m['detail']} |")

    overall_items = [fast["passed"], live["passed"]] + [m["passed"] for m in manual]
    overall_ok = all(item is not False for item in overall_items)
    lines += [
        "",
        "## Summary",
        "",
        "All checks passed." if overall_ok else "One or more checks FAILED — see above.",
    ]
    return "\n".join(lines) + "\n"
