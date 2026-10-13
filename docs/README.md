# Hop 3 Documentation

Hop 3 is the Dialogflow CX adapter behind the A2A gateway. It exposes one HTTP+JSON A2A endpoint, resolves a requested capability to a configured skill agent, and forwards the caller's utterance to Dialogflow CX.

## Documents

- [Configuration](configuration.md): environment variables, registry format, authentication, and startup checks.
- [A2A Support](a2a-support.md): agent card, supported operations, handoff payload, and capability behavior.
- [Skill Agent Architecture](skill-agent-architecture.md): routing workflow, integration boundaries, and scale-out model.

## Local endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /healthz` | Reports adapter health and loaded agent count. |
| `GET /a2a/.well-known/agent-card.json` | Publishes A2A metadata and registered skills. |
| `POST /a2a/message:send` | Accepts a structured handoff and invokes Dialogflow CX. |

Run with:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8001
```