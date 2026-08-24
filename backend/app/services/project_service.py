from sqlalchemy.orm import Session

from backend.app.models.project import Project


def create_project(
    db: Session,
    name: str,
    description: str | None,
    owner_id: int,
) -> Project:
    project = Project(
        name=name,
        description=description,
        owner_id=owner_id,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project
def get_user_projects(
    db: Session,
    owner_id: int,
) -> list[Project]:
    return (
        db.query(Project)
        .filter(Project.owner_id == owner_id)
        .all()
    )
def get_project(
    db: Session,
    project_id: int,
    owner_id: int,
) -> Project | None:
    return (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == owner_id,
        )
        .first()
    )
def delete_project(
    db: Session,
    project: Project,
) -> None:
    db.delete(project)
    db.commit()
def update_project(
    db: Session,
    project: Project,
    name: str | None,
    description: str | None,
) -> Project:
    if name is not None:
        project.name = name

    if description is not None:
        project.description = description

    db.commit()
    db.refresh(project)

    return project