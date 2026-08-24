from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.meeting import Meeting
from backend.app.models.meeting_participant import MeetingParticipant
from backend.app.models.team import Team
from backend.app.models.team_member import TeamMember
from backend.app.models.user import User


# ============================================================
# MEETINGS
# ============================================================

def create_meeting(
    db: Session,
    title: str,
    description: str | None,
    start_time: datetime,
    end_time: datetime,
    organizer_id: int,
    team_id: int | None = None,
) -> Meeting:

    meeting = Meeting(
        title=title,
        description=description,
        start_time=start_time,
        end_time=end_time,
        organizer_id=organizer_id,
        team_id=team_id,
    )

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return meeting


def get_user_meetings(
    db: Session,
    user_id: int,
) -> list[Meeting]:

    # Meetings organized by the user
    organized = (
        db.query(Meeting)
        .filter(
            Meeting.organizer_id == user_id
        )
    )

    # Meetings where the user is a participant
    participated = (
        db.query(Meeting)
        .join(
            MeetingParticipant,
            MeetingParticipant.meeting_id == Meeting.id,
        )
        .filter(
            MeetingParticipant.user_id == user_id
        )
    )

    meetings = organized.union(participated).order_by(
        Meeting.start_time.asc()
    ).all()

    return meetings


def get_meeting(
    db: Session,
    meeting_id: int,
) -> Meeting | None:

    return (
        db.query(Meeting)
        .filter(
            Meeting.id == meeting_id
        )
        .first()
    )


def delete_meeting(
    db: Session,
    meeting: Meeting,
) -> None:

    db.delete(meeting)
    db.commit()


# ============================================================
# TEAM ACCESS
# ============================================================

def get_team(
    db: Session,
    team_id: int,
) -> Team | None:

    return (
        db.query(Team)
        .filter(
            Team.id == team_id
        )
        .first()
    )


def is_team_member(
    db: Session,
    team_id: int,
    user_id: int,
) -> bool:

    team = get_team(
        db=db,
        team_id=team_id,
    )

    if team is None:
        return False

    # Team owner automatically has access
    if team.owner_id == user_id:
        return True

    member = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
        .first()
    )

    return member is not None


# ============================================================
# PARTICIPANTS
# ============================================================

def add_participant(
    db: Session,
    meeting_id: int,
    user_id: int,
) -> MeetingParticipant:

    existing = (
        db.query(MeetingParticipant)
        .filter(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id == user_id,
        )
        .first()
    )

    if existing:
        raise ValueError(
            "User is already a participant."
        )

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if user is None:
        raise ValueError(
            "User not found."
        )

    participant = MeetingParticipant(
        meeting_id=meeting_id,
        user_id=user_id,
        status="invited",
    )

    db.add(participant)
    db.commit()
    db.refresh(participant)

    return participant


def get_meeting_participants(
    db: Session,
    meeting_id: int,
) -> list[MeetingParticipant]:

    return (
        db.query(MeetingParticipant)
        .filter(
            MeetingParticipant.meeting_id == meeting_id
        )
        .all()
    )


def get_participant(
    db: Session,
    meeting_id: int,
    user_id: int,
) -> MeetingParticipant | None:

    return (
        db.query(MeetingParticipant)
        .filter(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id == user_id,
        )
        .first()
    )


def update_participant_status(
    db: Session,
    participant: MeetingParticipant,
    status: str,
) -> MeetingParticipant:

    allowed_statuses = {
        "invited",
        "accepted",
        "declined",
        "joined",
        "left",
    }

    if status not in allowed_statuses:
        raise ValueError(
            "Invalid participant status."
        )

    participant.status = status

    if status == "joined":
        participant.joined_at = datetime.utcnow()

    db.commit()
    db.refresh(participant)

    return participant


def remove_participant(
    db: Session,
    participant: MeetingParticipant,
) -> None:

    db.delete(participant)
    db.commit()