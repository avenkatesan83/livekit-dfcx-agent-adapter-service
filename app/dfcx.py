import asyncio
from typing import Any

from google.api_core.client_options import ClientOptions
from google.cloud import dialogflowcx_v3 as dialogflowcx
from google.protobuf.json_format import MessageToDict

from app.models import DFCXSkillAgent

# Plain text, not a WELCOME event: agents are not required to define an event handler.
WELCOME_UTTERANCE = "hi"
_START_PAGE_SUFFIX = "/pages/START_PAGE"


class DFCXClient:
    def __init__(self, skill_agent: DFCXSkillAgent):
        self.skill_agent = skill_agent
        client_options = None
        if skill_agent.location != "global":
            client_options = ClientOptions(api_endpoint=f"{skill_agent.location}-dialogflow.googleapis.com")
        self.client = dialogflowcx.SessionsClient(client_options=client_options)

    def _send(self, session: str, query_input: dict[str, Any], parameters: dict[str, Any]):
        return self.client.detect_intent(
            request={
                "session": session,
                "query_input": query_input,
                "query_params": {"parameters": parameters},
            }
        )

    @staticmethod
    def _needs_welcome(query_result) -> bool:
        """A fresh CX session sits on START_PAGE with no active routes until a welcome turn runs."""
        return (
            query_result.match.match_type == dialogflowcx.Match.MatchType.NO_MATCH
            and query_result.current_page.name.endswith(_START_PAGE_SUFFIX)
        )

    def _detect_intent(
        self, session_id: str, capability: str, query_text: str, user_context: dict[str, Any]
    ) -> dict[str, Any]:
        agent = self.skill_agent
        session = (
            f"projects/{agent.project_id}/locations/{agent.location}/agents/"
            f"{agent.agent_id}/environments/{agent.environment}/sessions/{session_id}"
        )
        parameters = {
            "ani": user_context.get("ani"),
            "caller_name": user_context.get("caller_name"),
            "authenticated": user_context.get("authenticated", False),
        }
        parameters = {key: value for key, value in parameters.items() if value is not None}
        text_input = {"text": {"text": query_text}, "language_code": agent.language_code}

        response = self._send(session, text_input, parameters)
        primed = self._needs_welcome(response.query_result)
        if primed:
            welcome_input = {"text": {"text": WELCOME_UTTERANCE}, "language_code": agent.language_code}
            self._send(session, welcome_input, parameters)
            response = self._send(session, text_input, parameters)

        query_result = response.query_result
        response_data = MessageToDict(query_result._pb, preserving_proto_field_name=False)
        response_data["status"] = "completed"
        response_data["provider"] = "dialogflow-cx"
        response_data["capability"] = capability
        response_data["sessionId"] = session_id
        response_data["dfcxSession"] = session
        response_data["skillAgentId"] = agent.id
        response_data["primed"] = primed
        return response_data

    async def detect_intent(
        self, session_id: str, capability: str, query_text: str, user_context: dict[str, Any]
    ) -> dict[str, Any]:
        return await asyncio.to_thread(self._detect_intent, session_id, capability, query_text, user_context)
