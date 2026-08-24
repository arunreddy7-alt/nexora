from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AgentOutputResponse(BaseModel):
    id: int
    project_id: int
    agent_type: str
    output: dict[str, Any]
    version: int
    created_at: datetime