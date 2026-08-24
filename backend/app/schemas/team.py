from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TeamCreate(BaseModel):
    name: str


class TeamResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    name: str
    owner_id: int
    created_at: datetime


class TeamMemberCreate(BaseModel):
    user_id: int
    role: str = "member"


class TeamMemberResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    team_id: int
    user_id: int
    role: str
    joined_at: datetime