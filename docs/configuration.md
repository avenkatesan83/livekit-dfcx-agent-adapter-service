# Configuration

Settings are loaded from `.env` and the process environment when the application starts. `config/skill_agents.json` is loaded at startup; invalid JSON, invalid models, duplicate IDs, duplicate capabilities, or missing downstream IDs stop startup.

## Environment variables

| Variable | Default | Required | Use |
| --- | --- | --- | --- |
| `ITSS_DFCX_PROJECT_ID` | empty | Yes | Google Cloud project for the IT Service Desk agent. |
| `ITSS_DFCX_AGENT_ID` | empty | Yes | Dialogflow CX agent ID for the IT Service Desk route. |
| `ITSS_DFCX_LOCATION` | `global` | No | Dialogflow CX region and API endpoint selection. |
| `ITSS_DFCX_ENVIRONMENT` | `draft` | No | Dialogflow CX environment. |
| `ITSS_DFCX_LANGUAGE_CODE` | `en-US` | No | Query language sent to Dialogflow CX. |
| `A2A_API_KEY` | empty | No | When set, requires matching `x-api-key` on message requests. |
| `DFCX_ADAPTER_PUBLIC_URL` | `http://127.0.0.1:8001/a2a` | No | URL published in the A2A agent card. |
| `DFCX_SKILL_AGENTS_PATH` | `config/skill_agents.json` | No | Registry file path. |

Additional registry entries use their own environment placeholders, such as `HRSS_DFCX_PROJECT_ID` and `FSS_DFCX_AGENT_ID`.

## Registry format

Each `skill_agents` entry contains:

```json
{
  "id": "itss-dialogflow-cx",
  "name": "IT Service Desk Dialogflow CX",
  "description": "Handles IT Service Desk requests.",
  "capabilities": ["it service desk"],
  "project_id": "${ITSS_DFCX_PROJECT_ID}",
  "agent_id": "${ITSS_DFCX_AGENT_ID}",
  "location": "${ITSS_DFCX_LOCATION}",
  "environment": "${ITSS_DFCX_ENVIRONMENT}",
  "language_code": "${ITSS_DFCX_LANGUAGE_CODE}",
  "enabled": true
}
```

Capability matching is case-insensitive, trims whitespace, converts underscores to spaces, and collapses repeated spaces. A capability may belong to only one enabled agent.

## Google authentication

The Dialogflow CX client uses Google Application Default Credentials. Authenticate separately with ADC or set `GOOGLE_APPLICATION_CREDENTIALS` to a service-account credential path. The credential must be allowed to detect intents for each configured agent.