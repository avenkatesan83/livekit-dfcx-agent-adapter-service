from functools import lru_cache
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    project_id: str = os.getenv("ITSS_DFCX_PROJECT_ID", "")
    agent_id: str = os.getenv("ITSS_DFCX_AGENT_ID", "")
    location: str = os.getenv("ITSS_DFCX_LOCATION", "global")
    environment: str = os.getenv("ITSS_DFCX_ENVIRONMENT", "draft")
    language_code: str = os.getenv("ITSS_DFCX_LANGUAGE_CODE", "en-US")
    a2a_api_key: str = os.getenv("A2A_API_KEY", "")
    public_url: str = os.getenv("DFCX_ADAPTER_PUBLIC_URL", "http://127.0.0.1:8001/a2a")
    skill_agents_config_path: str = os.getenv("DFCX_SKILL_AGENTS_PATH", "config/skill_agents.json")

    def validate_dialogflow(self) -> None:
        missing = [
            name
            for name, value in {
                "ITSS_DFCX_PROJECT_ID": self.project_id,
                "ITSS_DFCX_AGENT_ID": self.agent_id,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing Dialogflow CX configuration: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
