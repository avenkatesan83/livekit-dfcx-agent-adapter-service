# DFCX Agent Adapter

Hop 3 exposes the A2A worker endpoint consumed by the A2A gateway.

## Run

```powershell
Copy-Item .env.example .env
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[test]"
# Authenticate Google Cloud separately with ADC or set GOOGLE_APPLICATION_CREDENTIALS.
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

The gateway should use `http://127.0.0.1:8001/a2a` as the skill endpoint. The adapter accepts `A2A-Version: 1.0` and handles `POST /a2a/message:send`.
