from pathlib import Path

import pytest

SAMPLE = Path(__file__).resolve().parent.parent / "samples" / "surefire-report.xml"


@pytest.fixture
def sample_xml() -> str:
    return SAMPLE.read_text(encoding="utf-8")
