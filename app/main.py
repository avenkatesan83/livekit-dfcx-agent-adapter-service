import logging
import time
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, status

from app.config import get_settings
from app.dfcx import DFCXClient
from app.models import HandoffRequest, SendMessageRequest
from app.observability import configure_logging, log_event
from app.registry import SkillAgentNotFoundError, SkillAgentRegistry

configure_logging("INFO")
logger = logging.getLogger("dfcx-adapter")
settings = get_settings()
registry = SkillAgentRegistry(settings.skill_agents_config_path)
registry.load()
log_event(logger, "skill_agent_registry_loaded", agents=registry.agent_count)

app = FastAPI(title="DFCX A2A Adapter", version="0.1.0")


def require_a2a_auth(a2a_version: str | None = Header(default=None, alias="A2A-Version"), x_api_key: str | None = Header(default=None, alias="x-api-key")) -> None:
    if a2a_version != "1.0":
        raise HTTPException(status_code=400, detail="A2A-Version '1.0' is required")
    if settings.a2a_api_key and x_api_key != settings.a2a_api_key:
        raise HTTPException(status_code=401, detail="A valid A2A API key is required")


def extract_handoff(request: SendMessageRequest) -> HandoffRequest:
    for part in request.message.parts:
        if isinstance(part.data, dict):
            return HandoffRequest.model_validate(part.data)
    raise ValueError("A2A message must contain a structured handoff in a data part")


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"status": "ok", "skill_agents_loaded": registry.agent_count}


@app.get("/a2a/.well-known/agent-card.json")
def agent_card() -> dict[str, Any]:
    return {
        "name": "IT Service Desk Dialogflow CX",
        "description": "Dialogflow CX adapter for IT Service Desk capabilities.",
        "supportedInterfaces": [{
            "url": settings.public_url,
            "protocolBinding": "HTTP+JSON",
            "protocolVersion": "1.0",
        }],
        "capabilities": {"streaming": False, "pushNotifications": False},
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json"],
        "skills": [
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description or f"Delegates requests for: {', '.join(agent.capabilities)}",
                "tags": agent.capabilities,
            }
            for agent in registry.list_agents()
        ],
    }


@app.post("/a2a/message:send", dependencies=[Depends(require_a2a_auth)])
async def send_message(request: SendMessageRequest) -> dict[str, Any]:
    started = time.perf_counter()
    handoff = None
    try:
        handoff = extract_handoff(request)
        skill_agent = registry.resolve(handoff.capability)
        log_event(
            logger,
            "handoff_received",
            lk_session_id=handoff.session_id,
            context_id=request.message.context_id,
            message_id=request.message.message_id,
            capability=handoff.capability,
            utterance=handoff.utterance,
            source=handoff.source,
            skill_agent_id=skill_agent.id,
            dfcx_project=skill_agent.project_id,
            dfcx_agent_id=skill_agent.agent_id,
            dfcx_environment=skill_agent.environment,
        )
        result = await DFCXClient(skill_agent).detect_intent(
            session_id=handoff.session_id,
            capability=handoff.capability,
            query_text=handoff.utterance or handoff.capability,
            user_context=handoff.user_context.model_dump(),
        )
    except ValueError as exc:
        log_event(logger, "handoff_invalid", level=logging.ERROR, error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SkillAgentNotFoundError as exc:
        log_event(logger, "skill_agent_not_found", level=logging.ERROR, capability=str(exc))
        raise HTTPException(status_code=404, detail=f"No DFCX skill agent registered for capability '{exc}'") from exc
    except Exception as exc:
        logger.exception(
            "dfcx_request_failed",
            extra={"event_fields": {
                "lk_session_id": getattr(handoff, "session_id", None),
                "context_id": request.message.context_id,
                "utterance": getattr(handoff, "utterance", None),
                "error": str(exc),
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            }},
        )
        raise HTTPException(status_code=502, detail="Dialogflow CX request failed") from exc

    match = result.get("match") or {}
    log_event(
        logger,
        "dfcx_result",
        lk_session_id=handoff.session_id,
        context_id=request.message.context_id,
        dfcx_session=result.get("dfcxSession"),
        utterance=handoff.utterance,
        status=result.get("status"),
        match_type=match.get("matchType"),
        intent=(match.get("intent") or {}).get("displayName"),
        confidence=result.get("intentDetectionConfidence"),
        page=(result.get("currentPage") or {}).get("displayName"),
        primed=result.get("primed"),
        reply=" ".join(
            text
            for message in result.get("responseMessages") or []
            for text in ((message.get("text") or {}).get("text") or [])
        )
        or None,
        duration_ms=round((time.perf_counter() - started) * 1000, 1),
    )
    return result
