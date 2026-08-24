from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int
    team_id: int | None
    created_at: datetime


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ProjectTeamAssign(BaseModel):
    team_id: int