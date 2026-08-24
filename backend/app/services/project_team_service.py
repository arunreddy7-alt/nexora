from sqlalchemy.orm import Session

from backend.app.models.project import Project
from backend.app.models.team import Team
from backend.app.models.team_member import TeamMember


def is_team_member(
    db: Session,
    team_id: int,
    user_id: int,
) -> bool:
    return (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
        .first()
        is not None
    )


def assign_project_to_team(
    db: Session,
    project: Project,
    team: Team,
) -> Project:
    project.team_id = team.id

    db.commit()
    db.refresh(project)

    return project


def remove_project_from_team(
    db: Session,
    project: Project,
) -> Project:
    project.team_id = None

    db.commit()
    db.refresh(project)

    return project


def get_team_projects(
    db: Session,
    team_id: int,
) -> list[Project]:
    return (
        db.query(Project)
        .filter(Project.team_id == team_id)
        .all()
    )