import json

from app.parser import parse_junit_xml
from app.summarizer import LLMError, Summarizer


class FakeLLM:
    """Returns a canned response; records what it was asked."""

    def __init__(self, reply: str | Exception):
        self.reply = reply
        self.calls = 0

    def complete(self, system: str, user: str) -> str:
        self.calls += 1
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def _llm_reply(n: int) -> str:
    return json.dumps(
        {
            "overall_summary": "Three tests failed for different reasons.",
            "analyses": [
                {
                    "test_name": f"t{i}",
                    "likely_cause": "cause",
                    "suggested_fix": "fix",
                    "severity": "medium",
                }
                for i in range(n)
            ],
        }
    )


def test_heuristic_mode_without_llm(sample_xml):
    result = Summarizer(llm=None).summarize(parse_junit_xml(sample_xml))
    assert result.source == "heuristic"
    assert len(result.analyses) == 3
    by_name = {a.test_name.split(".")[-1]: a for a in result.analyses}
    assert by_name["sendsConfirmationEmail"].severity == "high"          # NPE rule
    assert "time" in by_name["fetchesInventoryFromWarehouse"].likely_cause.lower()


def test_llm_mode_uses_model_output(sample_xml):
    llm = FakeLLM(_llm_reply(3))
    result = Summarizer(llm=llm).summarize(parse_junit_xml(sample_xml))
    assert result.source == "llm"
    assert result.overall_summary.startswith("Three tests")
    assert llm.calls == 1


def test_llm_output_inside_code_fence_is_accepted(sample_xml):
    llm = FakeLLM("```json\n" + _llm_reply(3) + "\n```")
    assert Summarizer(llm=llm).summarize(parse_junit_xml(sample_xml)).source == "llm"


def test_falls_back_when_llm_raises(sample_xml):
    result = Summarizer(llm=FakeLLM(LLMError("boom"))).summarize(parse_junit_xml(sample_xml))
    assert result.source == "heuristic"


def test_falls_back_on_garbage_output(sample_xml):
    result = Summarizer(llm=FakeLLM("not json")).summarize(parse_junit_xml(sample_xml))
    assert result.source == "heuristic"


def test_falls_back_when_analysis_count_is_wrong(sample_xml):
    result = Summarizer(llm=FakeLLM(_llm_reply(1))).summarize(parse_junit_xml(sample_xml))
    assert result.source == "heuristic"


def test_max_failures_limits_analyses(sample_xml):
    result = Summarizer(llm=None).summarize(parse_junit_xml(sample_xml), max_failures=2)
    assert len(result.analyses) == 2


def test_all_passing_skips_llm():
    llm = FakeLLM(_llm_reply(0))
    report = parse_junit_xml('<testsuite><testcase classname="A" name="ok"/></testsuite>')
    result = Summarizer(llm=llm).summarize(report)
    assert llm.calls == 0
    assert "passed" in result.overall_summary
