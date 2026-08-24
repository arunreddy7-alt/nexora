from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MeetingCreate(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    team_id: int | None = None


class MeetingResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    title: str
    description: str | None
    start_time: datetime
    end_time: datetime
    organizer_id: int
    team_id: int | None
    created_at: datetime


class MeetingParticipantCreate(BaseModel):
    user_id: int


class MeetingParticipantResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    meeting_id: int
    user_id: int
    status: str
    joined_at: datetime | None


class MeetingParticipantStatusUpdate(BaseModel):
    status: str