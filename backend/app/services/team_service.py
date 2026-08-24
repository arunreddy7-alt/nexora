from sqlalchemy.orm import Session

from backend.app.models.team import Team
from backend.app.models.team_member import TeamMember
from backend.app.models.user import User


def create_team(
    db: Session,
    name: str,
    owner_id: int,
) -> Team:

    team = Team(
        name=name,
        owner_id=owner_id,
    )

    db.add(team)
    db.commit()
    db.refresh(team)

    # Automatically make the owner a team member.
    owner_membership = TeamMember(
        team_id=team.id,
        user_id=owner_id,
        role="owner",
    )

    db.add(owner_membership)
    db.commit()
    db.refresh(team)

    return team


def get_user_teams(
    db: Session,
    user_id: int,
) -> list[Team]:

    return (
        db.query(Team)
        .outerjoin(
            TeamMember,
            TeamMember.team_id == Team.id,
        )
        .filter(
            (Team.owner_id == user_id)
            | (TeamMember.user_id == user_id)
        )
        .distinct()
        .all()
    )


def get_team(
    db: Session,
    team_id: int,
) -> Team | None:

    return (
        db.query(Team)
        .filter(Team.id == team_id)
        .first()
    )


def is_team_owner(
    team: Team,
    user_id: int,
) -> bool:

    return team.owner_id == user_id


def add_team_member(
    db: Session,
    team_id: int,
    user_id: int,
    role: str = "member",
) -> TeamMember:

    existing_member = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
        .first()
    )

    if existing_member:
        raise ValueError(
            "User is already a member of this team."
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise ValueError(
            "User not found."
        )

    membership = TeamMember(
        team_id=team_id,
        user_id=user_id,
        role=role,
    )

    db.add(membership)
    db.commit()
    db.refresh(membership)

    return membership


def get_team_members(
    db: Session,
    team_id: int,
) -> list[TeamMember]:

    return (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id
        )
        .all()
    )


def remove_team_member(
    db: Session,
    team_id: int,
    user_id: int,
) -> bool:

    membership = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
        .first()
    )

    if membership is None:
        return False

    # Do not allow the owner membership
    # to be removed through this endpoint.
    if membership.role == "owner":
        raise ValueError(
            "The team owner cannot be removed."
        )

    db.delete(membership)
    db.commit()

    return True


def delete_team(
    db: Session,
    team: Team,
) -> None:

    db.delete(team)
    db.commit()