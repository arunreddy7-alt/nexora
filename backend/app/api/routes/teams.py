from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from backend.app.api.dependencies import (
    get_current_user,
    get_db,
)

from backend.app.models.user import User

from backend.app.schemas.team import (
    TeamCreate,
    TeamMemberCreate,
    TeamMemberResponse,
    TeamResponse,
)

from backend.app.schemas.project import (
    ProjectResponse,
)

from backend.app.services.team_service import (
    add_team_member,
    create_team,
    delete_team,
    get_team,
    get_team_members,
    get_user_teams,
    is_team_owner,
    remove_team_member,
)

from backend.app.services.project_team_service import (
    get_team_projects,
    is_team_member,
)


router = APIRouter(
    prefix="/teams",
    tags=["Teams"],
)


# ============================================================
# CREATE TEAM
# ============================================================

@router.post(
    "",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_team_endpoint(
    team_data: TeamCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    if not team_data.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Team name cannot be empty.",
        )

    return create_team(
        db=db,
        name=team_data.name.strip(),
        owner_id=current_user.id,
    )


# ============================================================
# GET MY TEAMS
# ============================================================

@router.get(
    "",
    response_model=list[TeamResponse],
)
def get_teams(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    return get_user_teams(
        db=db,
        user_id=current_user.id,
    )


# ============================================================
# GET TEAM PROJECTS
#
# IMPORTANT:
# This must appear BEFORE /{team_id}
# ============================================================

@router.get(
    "/{team_id}/projects",
    response_model=list[ProjectResponse],
)
def get_projects_for_team(
    team_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    team = get_team(
        db=db,
        team_id=team_id,
    )

    if team is None:
        raise HTTPException(
            status_code=404,
            detail="Team not found.",
        )

    if not is_team_member(
        db=db,
        team_id=team_id,
        user_id=current_user.id,
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "You are not a member "
                "of this team."
            ),
        )

    return get_team_projects(
        db=db,
        team_id=team_id,
    )


# ============================================================
# GET TEAM
# ============================================================

@router.get(
    "/{team_id}",
    response_model=TeamResponse,
)
def get_team_endpoint(
    team_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    team = get_team(
        db=db,
        team_id=team_id,
    )

    if team is None:
        raise HTTPException(
            status_code=404,
            detail="Team not found.",
        )

    user_teams = get_user_teams(
        db=db,
        user_id=current_user.id,
    )

    if team not in user_teams:
        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have access "
                "to this team."
            ),
        )

    return team


# ============================================================
# ADD MEMBER
# ============================================================

@router.post(
    "/{team_id}/members",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    team_id: int,
    member_data: TeamMemberCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    team = get_team(
        db=db,
        team_id=team_id,
    )

    if team is None:
        raise HTTPException(
            status_code=404,
            detail="Team not found.",
        )

    if not is_team_owner(
        team,
        current_user.id,
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Only the team owner "
                "can add members."
            ),
        )

    try:
        return add_team_member(
            db=db,
            team_id=team_id,
            user_id=member_data.user_id,
            role=member_data.role,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


# ============================================================
# GET TEAM MEMBERS
# ============================================================

@router.get(
    "/{team_id}/members",
    response_model=list[TeamMemberResponse],
)
def get_members(
    team_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    team = get_team(
        db=db,
        team_id=team_id,
    )

    if team is None:
        raise HTTPException(
            status_code=404,
            detail="Team not found.",
        )

    user_teams = get_user_teams(
        db=db,
        user_id=current_user.id,
    )

    if team not in user_teams:
        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have access "
                "to this team."
            ),
        )

    return get_team_members(
        db=db,
        team_id=team_id,
    )


# ============================================================
# REMOVE MEMBER
# ============================================================

@router.delete(
    "/{team_id}/members/{user_id}",
)
def remove_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    team = get_team(
        db=db,
        team_id=team_id,
    )

    if team is None:
        raise HTTPException(
            status_code=404,
            detail="Team not found.",
        )

    if not is_team_owner(
        team,
        current_user.id,
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Only the team owner "
                "can remove members."
            ),
        )

    try:
        removed = remove_team_member(
            db=db,
            team_id=team_id,
            user_id=user_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if not removed:
        raise HTTPException(
            status_code=404,
            detail="Team member not found.",
        )

    return {
        "message": (
            "Team member removed successfully."
        )
    }


# ============================================================
# DELETE TEAM
# ============================================================

@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_team_endpoint(
    team_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    team = get_team(
        db=db,
        team_id=team_id,
    )

    if team is None:
        raise HTTPException(
            status_code=404,
            detail="Team not found.",
        )

    if not is_team_owner(
        team,
        current_user.id,
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Only the team owner "
                "can delete the team."
            ),
        )

    delete_team(
        db=db,
        team=team,
    )