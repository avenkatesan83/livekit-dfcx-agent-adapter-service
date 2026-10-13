# A2A Support

The adapter supports A2A protocol version `1.0` over HTTP+JSON.

## Agent card

`GET /a2a/.well-known/agent-card.json` publishes:

- interface URL from `DFCX_ADAPTER_PUBLIC_URL`;
- protocol binding `HTTP+JSON` and version `1.0`;
- JSON input and output modes;
- registered enabled skill agents and their capability tags;
- `streaming: false` and `pushNotifications: false`.

## Message request

`POST /a2a/message:send` requires the `A2A-Version: 1.0` header. If `A2A_API_KEY` is configured, it also requires `x-api-key`.

The A2A message must contain a `data` part with this handoff object:

```json
{
  "handoff_version": "1",
  "source": "itss-steering-agent",
  "session_id": "session-123",
  "capability": "it service desk",
  "utterance": "I need to reset my password",
  "user_context": {
    "ani": "+14165551234",
    "caller_name": "Alex",
    "authenticated": true
  }
}
```

`utterance` is optional. When omitted, the capability string is sent to Dialogflow CX as the query text. `user_context` carries `ani`, `caller_name`, and `authenticated` into Dialogflow CX session parameters; extra user context fields are accepted.

## Responses and errors

Successful responses return the Dialogflow CX query result plus adapter fields including `status`, `provider`, `capability`, `sessionId`, `dfcxSession`, `skillAgentId`, and `primed`.

| Status | Meaning |
| --- | --- |
| `200` | Dialogflow CX returned a result. |
| `400` | Missing/incorrect A2A version or invalid handoff. |
| `401` | API key is configured but invalid or missing. |
| `404` | No enabled skill agent owns the requested capability. |
| `502` | Dialogflow CX or another downstream request failed. |

Each request reuses `session_id` to preserve Dialogflow CX conversation state. A new CX session is automatically primed with a plain-text `hi` turn when the first response is an unmatched `START_PAGE` result.