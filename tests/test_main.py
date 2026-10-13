from fastapi.testclient import TestClient

from app.main import app


class FakeDFCXClient:
    def __init__(self, settings):
        self.settings = settings

    async def detect_intent(self, session_id, capability, query_text, user_context):
        return {
            "status": "completed",
            "provider": "dialogflow-cx",
            "sessionId": session_id,
            "capability": capability,
            "queryText": query_text,
            "userContext": user_context,
        }


def test_message_send_maps_handoff_to_dfcx(monkeypatch):
    monkeypatch.setattr("app.main.DFCXClient", FakeDFCXClient)
    response = TestClient(app).post(
        "/a2a/message:send",
        headers={"A2A-Version": "1.0"},
        json={
            "message": {
                "messageId": "message-123",
                "role": "ROLE_USER",
                "contextId": "session-123",
                "parts": [{
                    "data": {
                        "handoff_version": "1",
                        "source": "itss-steering-agent",
                        "session_id": "session-123",
                        "capability": "it service desk",
                        "utterance": "I need to reset my password",
                        "user_context": {
                            "ani": "+14165551234",
                            "caller_name": "Alex",
                            "authenticated": True,
                        },
                    },
                    "mediaType": "application/json",
                }],
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["sessionId"] == "session-123"
    assert response.json()["queryText"] == "I need to reset my password"
    assert response.json()["userContext"]["authenticated"] is True


def test_message_send_falls_back_to_capability_when_utterance_missing(monkeypatch):
    monkeypatch.setattr("app.main.DFCXClient", FakeDFCXClient)
    response = TestClient(app).post(
        "/a2a/message:send",
        headers={"A2A-Version": "1.0"},
        json={
            "message": {
                "messageId": "message-password-reset",
                "role": "ROLE_USER",
                "contextId": "session-password-reset",
                "parts": [{
                    "data": {
                        "handoff_version": "1",
                        "source": "itss-steering-agent",
                        "session_id": "session-password-reset",
                        "capability": "it service desk",
                        "user_context": {"authenticated": True},
                    },
                    "mediaType": "application/json",
                }],
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["queryText"] == "it service desk"


def test_message_send_requires_a2a_version():
    response = TestClient(app).post("/a2a/message:send", json={})

    assert response.status_code == 400
    assert "A2A-Version" in response.json()["detail"]
