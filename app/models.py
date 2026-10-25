"""Pydantic models: the data shapes used by the parser, summarizer and API."""
from typing import Literal

from pydantic import BaseModel, Field

MAX_REPORT_CHARS = 1_000_000  # reject absurdly large uploads early


class FailedCase(BaseModel):
    """One failed or errored test case extracted from a JUnit XML report."""

    test_class: str
    test_name: str
    kind: Literal["failure", "error"]
    message: str = ""
    stack_trace: str = ""


class ParsedReport(BaseModel):
    """Counts plus the list of failed cases."""

    total: int
    failed: int
    errors: int
    skipped: int
    failures: list[FailedCase]


class FailureAnalysis(BaseModel):
    """Analysis of a single failed test."""

    test_name: str
    likely_cause: str
    suggested_fix: str
    severity: Literal["low", "medium", "high"]


class LLMOutput(BaseModel):
    """The JSON shape we ask the LLM to return (validated on the way back)."""

    overall_summary: str
    analyses: list[FailureAnalysis]


class SummarizeRequest(BaseModel):
    report_xml: str = Field(min_length=1, max_length=MAX_REPORT_CHARS)
    max_failures: int = Field(default=10, ge=1, le=50)


class SummaryResponse(BaseModel):
    total: int
    failed: int
    errors: int
    skipped: int
    overall_summary: str
    analyses: list[FailureAnalysis]
    source: Literal["llm", "heuristic"]
    cached: bool = False
