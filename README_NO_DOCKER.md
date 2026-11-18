# Run AI Workflow Automation Platform Without Docker

This guide runs the existing project locally with SQLite and the deterministic FakeLLM.
No Docker, PostgreSQL server, Redis, or frontend is required for the MVP.

## 1. Prerequisites

- Python 3.11 or newer
- A terminal (macOS, Linux, or WSL) or Windows PowerShell

Check Python:

```bash
python --version
# On macOS/Linux/WSL you may need:
python3 --version
```

## 2. Extract and enter the project

```bash
unzip ai-workflow-platform-no-docker.zip
cd ai-workflow-platform
```

If you already extracted the archive, simply `cd` into the `ai-workflow-platform` folder.

## 3. Create and activate a virtual environment

macOS / Linux / WSL:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Upgrade pip and install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

## 4. Configure local settings

The app reads environment variables directly; it does not automatically load `.env`.
Set the following in **each terminal** used to run the API and worker.

macOS / Linux / WSL:

```bash
export DATABASE_URL="sqlite:///./local.db"
export LLM_PROVIDER="fake"
export MAX_AGENT_STEPS="5"
export MEMORY_WINDOW="10"
```

Windows PowerShell:

```powershell
$env:DATABASE_URL="sqlite:///./local.db"
$env:LLM_PROVIDER="fake"
$env:MAX_AGENT_STEPS="5"
$env:MEMORY_WINDOW="10"
```

`FakeLLM` is suitable for deterministic local tests. For real OpenAI calls, set
`LLM_PROVIDER=openai` and `OPENAI_API_KEY` to your own key in both terminals.
Never commit API keys.

## 5. Run tests

macOS / Linux / WSL:

```bash
DATABASE_URL=sqlite:// pytest -v
```

Windows PowerShell:

```powershell
$env:DATABASE_URL="sqlite://"
pytest -v
```

The project's local test suite uses SQLite and FakeLLM. The live-stack test is opt-in.

## 6. Start the API

Terminal 1 (activate the virtual environment and set the environment variables above):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- API documentation: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/health

## 7. Start the worker

Terminal 2: enter the same project directory, activate the same virtual environment,
and set the same `DATABASE_URL` and `LLM_PROVIDER` values. Then run:

```bash
python -m app.infra.worker
```

Keep one worker process when using SQLite. The worker polls the database for queued runs.

## 8. Test a synchronous request

macOS / Linux / WSL:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo","message":"Recommend what to reorder"}'
```

Windows PowerShell (use `curl.exe`):

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/agent/chat `
  -H "Content-Type: application/json" `
  -d '{\"session_id\":\"demo\",\"message\":\"Recommend what to reorder\"}'
```

## 9. Test an asynchronous workflow

Submit a run:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/workflows/runs \
  -H "Content-Type: application/json" \
  -d '{"session_id":"async-demo","message":"Recommend what to reorder"}'
```

Copy the returned `run_id`, then check it:

```bash
curl http://127.0.0.1:8000/api/v1/workflows/runs/RUN_ID
```

The worker should process the queued job and update its status.

## 10. Optional OpenAI integration

In both the API and worker terminals, configure:

```bash
export LLM_PROVIDER="openai"
export OPENAI_API_KEY="YOUR_API_KEY"
export OPENAI_MODEL="gpt-4o-mini"
```

PowerShell:

```powershell
$env:LLM_PROVIDER="openai"
$env:OPENAI_API_KEY="YOUR_API_KEY"
$env:OPENAI_MODEL="gpt-4o-mini"
```

Restart the API and worker after changing configuration.

## Notes and limitations

- The existing app initializes database tables on startup.
- SQLite is intended for local development and a single worker.
- Use PostgreSQL before running multiple workers or deploying for concurrent users.
- The repository includes Docker files for an optional Docker deployment; they are not needed for this guide.
- This is an MVP, not a hardened public production deployment. Add authentication, migrations,
  retry/recovery, rate limiting, monitoring, and secret management before exposing it publicly.
- Check `README.md` for the original architecture and roadmap, and `docs/TEST_REPORT.md`
  for the recorded test report.
