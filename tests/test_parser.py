import pytest

from app.parser import ReportParseError, parse_junit_xml


def test_parses_counts_and_failures(sample_xml):
    report = parse_junit_xml(sample_xml)
    assert report.total == 6
    assert report.failed == 2
    assert report.errors == 1
    assert report.skipped == 1
    assert [f.test_name for f in report.failures] == [
        "calculatesTotalWithTax",
        "sendsConfirmationEmail",
        "fetchesInventoryFromWarehouse",
    ]


def test_failure_kind_is_detected(sample_xml):
    report = parse_junit_xml(sample_xml)
    kinds = {f.test_name: f.kind for f in report.failures}
    assert kinds["fetchesInventoryFromWarehouse"] == "error"
    assert kinds["calculatesTotalWithTax"] == "failure"


def test_all_passing_report_has_no_failures():
    xml = '<testsuite><testcase classname="A" name="ok"/></testsuite>'
    report = parse_junit_xml(xml)
    assert report.total == 1 and report.failures == []


def test_invalid_xml_raises():
    with pytest.raises(ReportParseError):
        parse_junit_xml("<testsuite><testcase></testsuite>")


def test_report_without_testcases_raises():
    with pytest.raises(ReportParseError):
        parse_junit_xml("<testsuite></testsuite>")


def test_entity_expansion_attack_is_rejected():
    evil = '<!DOCTYPE x [<!ENTITY a "boom">]><testsuite><testcase name="&a;"/></testsuite>'
    with pytest.raises(ReportParseError):
        parse_junit_xml(evil)


def test_long_stack_trace_is_truncated():
    trace = "x" * 10_000
    xml = f'<testsuite><testcase classname="A" name="t"><failure message="m">{trace}</failure></testcase></testsuite>'
    report = parse_junit_xml(xml)
    assert len(report.failures[0].stack_trace) == 2000
