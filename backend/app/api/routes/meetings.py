from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import (
    get_current_user,
    get_db,
)

from backend.app.models.user import User

from backend.app.schemas.meeting import (
    MeetingCreate,
    MeetingResponse,
    MeetingParticipantCreate,
    MeetingParticipantResponse,
    MeetingParticipantStatusUpdate,
)

from backend.app.services.meeting_service import (
    create_meeting,
    get_user_meetings,
    get_meeting,
    delete_meeting,
    add_participant,
    get_meeting_participants,
    get_participant,
    update_participant_status,
    remove_participant,
    get_team,
    is_team_member,
)


router = APIRouter(
    prefix="/meetings",
    tags=["Meetings"],
)


# ============================================================
# CREATE MEETING
# ============================================================

@router.post(
    "",
    response_model=MeetingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_meeting_endpoint(
    meeting_data: MeetingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if not meeting_data.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Meeting title cannot be empty.",
        )

    if meeting_data.end_time <= meeting_data.start_time:
        raise HTTPException(
            status_code=400,
            detail="End time must be after start time.",
        )

    # --------------------------------------------------------
    # TEAM MEETING VALIDATION
    # --------------------------------------------------------

    if meeting_data.team_id is not None:

        team = get_team(
            db=db,
            team_id=meeting_data.team_id,
        )

        if team is None:
            raise HTTPException(
                status_code=404,
                detail="Team not found.",
            )

        if not is_team_member(
            db=db,
            team_id=meeting_data.team_id,
            user_id=current_user.id,
        ):
            raise HTTPException(
                status_code=403,
                detail="You must be a member of the team to create a team meeting.",
            )

    return create_meeting(
        db=db,
        title=meeting_data.title.strip(),
        description=meeting_data.description,
        start_time=meeting_data.start_time,
        end_time=meeting_data.end_time,
        organizer_id=current_user.id,
        team_id=meeting_data.team_id,
    )


# ============================================================
# GET MY MEETINGS
# ============================================================

@router.get(
    "",
    response_model=list[MeetingResponse],
)
def get_meetings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return get_user_meetings(
        db=db,
        user_id=current_user.id,
    )


# ============================================================
# GET MEETING
# ============================================================

@router.get(
    "/{meeting_id}",
    response_model=MeetingResponse,
)
def get_meeting_endpoint(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    meeting = get_meeting(
        db=db,
        meeting_id=meeting_id,
    )

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found.",
        )

    # Organizer always has access
    if meeting.organizer_id == current_user.id:
        return meeting

    # Team members can access team meetings
    if meeting.team_id is not None:

        if is_team_member(
            db=db,
            team_id=meeting.team_id,
            user_id=current_user.id,
        ):
            return meeting

    # Normal meeting participants can access
    participant = get_participant(
        db=db,
        meeting_id=meeting_id,
        user_id=current_user.id,
    )

    if participant is None:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this meeting.",
        )

    return meeting


# ============================================================
# DELETE MEETING
# ============================================================

@router.delete(
    "/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_meeting_endpoint(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    meeting = get_meeting(
        db=db,
        meeting_id=meeting_id,
    )

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found.",
        )

    if meeting.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the organizer can delete the meeting.",
        )

    delete_meeting(
        db=db,
        meeting=meeting,
    )


# ============================================================
# ADD PARTICIPANT
# ============================================================

@router.post(
    "/{meeting_id}/participants",
    response_model=MeetingParticipantResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_participant_endpoint(
    meeting_id: int,
    participant_data: MeetingParticipantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    meeting = get_meeting(
        db=db,
        meeting_id=meeting_id,
    )

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found.",
        )

    if meeting.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the organizer can add participants.",
        )

    # If this is a team meeting, participant must belong
    # to the same team.
    if meeting.team_id is not None:

        if not is_team_member(
            db=db,
            team_id=meeting.team_id,
            user_id=participant_data.user_id,
        ):
            raise HTTPException(
                status_code=400,
                detail="The user is not a member of this team.",
            )

    try:

        return add_participant(
            db=db,
            meeting_id=meeting_id,
            user_id=participant_data.user_id,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


# ============================================================
# GET PARTICIPANTS
# ============================================================

@router.get(
    "/{meeting_id}/participants",
    response_model=list[MeetingParticipantResponse],
)
def get_participants_endpoint(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    meeting = get_meeting(
        db=db,
        meeting_id=meeting_id,
    )

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found.",
        )

    has_access = False

    if meeting.organizer_id == current_user.id:
        has_access = True

    elif meeting.team_id is not None:
        has_access = is_team_member(
            db=db,
            team_id=meeting.team_id,
            user_id=current_user.id,
        )

    else:
        participant = get_participant(
            db=db,
            meeting_id=meeting_id,
            user_id=current_user.id,
        )

        has_access = participant is not None

    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this meeting.",
        )

    return get_meeting_participants(
        db=db,
        meeting_id=meeting_id,
    )


# ============================================================
# UPDATE MY PARTICIPANT STATUS
# ============================================================

@router.put(
    "/{meeting_id}/participants/me",
    response_model=MeetingParticipantResponse,
)
def update_my_participant_status(
    meeting_id: int,
    status_data: MeetingParticipantStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    meeting = get_meeting(
        db=db,
        meeting_id=meeting_id,
    )

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found.",
        )

    participant = get_participant(
        db=db,
        meeting_id=meeting_id,
        user_id=current_user.id,
    )

    if participant is None:
        raise HTTPException(
            status_code=404,
            detail="You are not a participant in this meeting.",
        )

    try:

        return update_participant_status(
            db=db,
            participant=participant,
            status=status_data.status,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


# ============================================================
# REMOVE PARTICIPANT
# ============================================================

@router.delete(
    "/{meeting_id}/participants/{user_id}",
)
def remove_participant_endpoint(
    meeting_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    meeting = get_meeting(
        db=db,
        meeting_id=meeting_id,
    )

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found.",
        )

    if meeting.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the organizer can remove participants.",
        )

    participant = get_participant(
        db=db,
        meeting_id=meeting_id,
        user_id=user_id,
    )

    if participant is None:
        raise HTTPException(
            status_code=404,
            detail="Participant not found.",
        )

    remove_participant(
        db=db,
        participant=participant,
    )

    return {
        "message": "Participant removed successfully."
    }