"""FastAPI entry point.

Run locally:  uvicorn app.main:app --reload
Docs UI:      http://127.0.0.1:8000/docs
"""
import logging
import os

from fastapi import FastAPI, HTTPException

from app.cache import ResponseCache
from app.models import SummarizeRequest, SummaryResponse
from app.parser import ReportParseError, parse_junit_xml
from app.summarizer import AnthropicLLM, Summarizer

logging.basicConfig(level=logging.INFO)

DEFAULT_MODEL = "claude-sonnet-5-5"


def build_default_summarizer() -> Summarizer:
    """Use the LLM only if an API key is configured; otherwise run offline."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return Summarizer(llm=None)
    model = os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
    return Summarizer(llm=AnthropicLLM(api_key=api_key, model=model))


def create_app(summarizer: Summarizer | None = None) -> FastAPI:
    """App factory: tests pass in a Summarizer with a fake LLM."""
    app = FastAPI(
        title="AI Test-Failure Summarizer",
        version="1.0.0",
        description="Summarises JUnit/Surefire XML failures with an LLM (or rules).",
    )
    active_summarizer = summarizer or build_default_summarizer()
    cache = ResponseCache(max_size=128)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/summarize", response_model=SummaryResponse)
    def summarize(request: SummarizeRequest) -> SummaryResponse:
        key = cache.make_key(request.report_xml, request.max_failures)
        cached = cache.get(key)
        if cached is not None:
            return cached.model_copy(update={"cached": True})

        try:
            report = parse_junit_xml(request.report_xml)
        except ReportParseError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        result = active_summarizer.summarize(report, request.max_failures)
        cache.set(key, result)
        return result

    return app


app = create_app()
