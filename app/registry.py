import json
import os
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from app.models import DFCXSkillAgent

_ENV_VAR_PATTERN = re.compile(r"\$\{(\w+)\}")


def _normalize_capability(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").split())


def _expand_env(value: Any) -> Any:
    """Recursively substitute ${VAR_NAME} placeholders with environment variables."""
    if isinstance(value, str):
        return _ENV_VAR_PATTERN.sub(lambda match: os.getenv(match.group(1), ""), value)
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    return value


class RegistryConfig(BaseModel):
    skill_agents: list[DFCXSkillAgent]


class SkillAgentNotFoundError(LookupError):
    pass


class SkillAgentRegistry:
    def __init__(self, config_path: str | Path):
        self._config_path = Path(config_path)
        self._agents: tuple[DFCXSkillAgent, ...] = ()
        self._by_capability: dict[str, DFCXSkillAgent] = {}

    def load(self) -> None:
        try:
            raw = json.loads(self._config_path.read_text(encoding="utf-8"))
            payload = _expand_env(raw)
            config = RegistryConfig.model_validate(payload)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise RuntimeError(f"Unable to load DFCX skill agent registry: {self._config_path}") from exc

        enabled_agents = [agent for agent in config.skill_agents if agent.enabled]
        seen_ids: set[str] = set()
        by_capability: dict[str, DFCXSkillAgent] = {}
        for agent in enabled_agents:
            if agent.id in seen_ids:
                raise RuntimeError(f"Duplicate skill agent id in registry: {agent.id}")
            seen_ids.add(agent.id)
            if not agent.project_id or not agent.agent_id:
                raise RuntimeError(f"Skill agent '{agent.id}' is missing project_id/agent_id configuration")
            for capability in agent.capabilities:
                normalized = _normalize_capability(capability)
                if normalized in by_capability:
                    raise RuntimeError(f"Capability '{normalized}' is claimed by multiple skill agents")
                by_capability[normalized] = agent

        self._agents = tuple(enabled_agents)
        self._by_capability = by_capability

    @property
    def is_loaded(self) -> bool:
        return bool(self._agents)

    @property
    def agent_count(self) -> int:
        return len(self._agents)

    def list_agents(self) -> tuple[DFCXSkillAgent, ...]:
        return self._agents

    def get(self, skill_id: str) -> DFCXSkillAgent:
        for agent in self._agents:
            if agent.id == skill_id:
                return agent
        raise SkillAgentNotFoundError(skill_id)

    def resolve(self, capability: str) -> DFCXSkillAgent:
        normalized = _normalize_capability(capability)
        agent = self._by_capability.get(normalized)
        if agent is None:
            raise SkillAgentNotFoundError(normalized)
        return agent
