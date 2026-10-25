import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.summarizer import Summarizer


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(Summarizer(llm=None)))


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_summarize_returns_analyses(client, sample_xml):
    response = client.post("/summarize", json={"report_xml": sample_xml})
    assert response.status_code == 200
    body = response.json()
    assert body["failed"] == 2 and body["errors"] == 1
    assert len(body["analyses"]) == 3
    assert body["cached"] is False


def test_second_identical_request_is_cached(client, sample_xml):
    client.post("/summarize", json={"report_xml": sample_xml})
    second = client.post("/summarize", json={"report_xml": sample_xml})
    assert second.json()["cached"] is True


def test_invalid_xml_returns_422(client):
    response = client.post("/summarize", json={"report_xml": "<nope"})
    assert response.status_code == 422


def test_empty_body_field_is_rejected(client):
    assert client.post("/summarize", json={"report_xml": ""}).status_code == 422


def test_max_failures_out_of_range_is_rejected(client, sample_xml):
    response = client.post("/summarize", json={"report_xml": sample_xml, "max_failures": 0})
    assert response.status_code == 422
