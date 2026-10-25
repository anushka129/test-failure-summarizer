# AI Test-Failure Summarizer

A small **Python / FastAPI** service that reads a JUnit/Surefire XML test report and returns a structured
summary of every failing test: likely cause, suggested fix and severity.

It uses an LLM (Anthropic API) when an API key is configured, and falls back to rule-based hints when there
is no key or the model call fails, so the service always returns a useful answer.

> Uses only sample data in `samples/`. Don't upload confidential reports to a third-party API.

## How it works

```
POST /summarize -> validate (Pydantic) -> cache lookup -> parse XML (defusedxml)
                                                              |
                     LLM (JSON output, validated) <-- Summarizer --> rule-based fallback
                                                              |
                                              cache store -> JSON response
```

## Run it

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API page. Expand `POST /summarize`, click
"Try it out" and paste the contents of `samples/surefire-report.xml` as the `report_xml` value.

To enable the LLM, set your key as an environment variable (never commit it):

```bash
export ANTHROPIC_API_KEY=sk-ant-...        # PowerShell: $env:ANTHROPIC_API_KEY="..."
```

Without a key, the service runs in offline `heuristic` mode. `.env.example` lists the settings.

## Tests

```bash
pytest -q          # 21 tests; no network or API key needed (the LLM is faked)
```

## Docker

```bash
docker build -t test-failure-summarizer .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY test-failure-summarizer
```

## Design decisions

- **`defusedxml`** for parsing, since reports are untrusted input (blocks XXE and entity-expansion attacks).
- **LLM behind a small interface** (`complete`), so tests use a fake and never hit the network.
- **Validated LLM output**: the reply must be valid JSON with the right number of analyses, otherwise we fall back.
- **Prompt-injection aware**: report text is passed as data inside tags, and the system prompt says to ignore instructions in it.
- **Bounded cost**: stack traces are truncated, `max_failures` is capped and identical requests are served from an LRU cache.
- **App factory** (`create_app`) allows dependency injection in tests.

## Project layout

```
app/
  main.py        FastAPI app, routes, wiring
  models.py      Pydantic request/response models
  parser.py      JUnit XML -> ParsedReport
  summarizer.py  LLM client, fallback rules, output validation
  cache.py       thread-safe LRU cache
tests/           pytest suite
samples/         example Surefire report
```
