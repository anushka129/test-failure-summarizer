"""Parse JUnit/Surefire XML reports into ParsedReport objects.

We use `defusedxml` instead of the standard library parser because report
files are untrusted input: defusedxml blocks XXE and "billion laughs" attacks.
"""
from defusedxml import ElementTree as ET

from app.models import FailedCase, ParsedReport

MAX_TRACE_CHARS = 2000  # keep LLM prompts (and cost) bounded


class ReportParseError(ValueError):
    """Raised when the XML is invalid or contains no test cases."""


def parse_junit_xml(xml_text: str) -> ParsedReport:
    try:
        root = ET.fromstring(xml_text)
    except (ET.ParseError, ValueError) as exc:  # ValueError covers defusedxml errors
        raise ReportParseError(f"Invalid or unsafe XML: {exc}") from exc

    cases = list(root.iter("testcase"))
    if not cases:
        raise ReportParseError("No <testcase> elements found in the report")

    failures: list[FailedCase] = []
    skipped = 0
    for case in cases:
        if case.find("skipped") is not None:
            skipped += 1
            continue
        for kind in ("failure", "error"):
            node = case.find(kind)
            if node is not None:
                failures.append(
                    FailedCase(
                        test_class=case.get("classname", "unknown"),
                        test_name=case.get("name", "unknown"),
                        kind=kind,
                        message=(node.get("message") or "")[:500],
                        stack_trace=(node.text or "").strip()[:MAX_TRACE_CHARS],
                    )
                )
                break  # a case is counted once

    return ParsedReport(
        total=len(cases),
        failed=sum(1 for f in failures if f.kind == "failure"),
        errors=sum(1 for f in failures if f.kind == "error"),
        skipped=skipped,
        failures=failures,
    )
