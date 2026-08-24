from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from fastapi.responses import FileResponse

from backend.app.services.download_service import (
    create_project_zip,
)

from backend.app.api.dependencies import (
    get_current_user,
    get_db,
)
from backend.app.models.user import User
from backend.app.models.team import Team

from backend.app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ProjectTeamAssign,
)

from backend.app.services.project_service import (
    create_project,
    get_user_projects,
    get_project,
    delete_project,
    update_project,
)

from backend.app.services.project_team_service import (
    assign_project_to_team,
    remove_project_from_team,
)


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


# ============================================================
# CREATE PROJECT
# ============================================================

@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project_endpoint(
    project_data: ProjectCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    project = create_project(
        db=db,
        name=project_data.name,
        description=project_data.description,
        owner_id=current_user.id,
    )

    return project


# ============================================================
# GET MY PROJECTS
# ============================================================

@router.get(
    "",
    response_model=list[ProjectResponse],
)
def get_projects(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    return get_user_projects(
        db=db,
        owner_id=current_user.id,
    )


# ============================================================
# ASSIGN PROJECT TO TEAM
# ============================================================

@router.put(
    "/{project_id}/team",
    response_model=ProjectResponse,
)
def assign_project_team(
    project_id: int,
    team_data: ProjectTeamAssign,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    project = get_project(
        db=db,
        project_id=project_id,
        owner_id=current_user.id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    team = (
        db.query(Team)
        .filter(
            Team.id == team_data.team_id
        )
        .first()
    )

    if team is None:
        raise HTTPException(
            status_code=404,
            detail="Team not found.",
        )

    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only the team owner can "
                "assign projects to the team."
            ),
        )

    return assign_project_to_team(
        db=db,
        project=project,
        team=team,
    )


# ============================================================
# REMOVE PROJECT FROM TEAM
# ============================================================

@router.delete(
    "/{project_id}/team",
    response_model=ProjectResponse,
)
def remove_project_team(
    project_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    project = get_project(
        db=db,
        project_id=project_id,
        owner_id=current_user.id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    if project.team_id is None:
        return project

    team = (
        db.query(Team)
        .filter(
            Team.id == project.team_id
        )
        .first()
    )

    if team is None:
        raise HTTPException(
            status_code=404,
            detail="Team not found.",
        )

    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only the team owner can "
                "remove the project."
            ),
        )

    return remove_project_from_team(
        db=db,
        project=project,
    )

    # ==========================================================
# DOWNLOAD PROJECT
# ==========================================================

@router.get(
    "/{project_id}/download",
)
def download_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project(
        db=db,
        project_id=project_id,
        owner_id=current_user.id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    try:
        zip_path = create_project_zip(
            project_id=project_id,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not create project ZIP: {exc}",
        )

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=f"{project.name.replace(' ', '_')}.zip",
    )

# ============================================================
# GET PROJECT
# ============================================================

@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project_by_id(
    project_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    project = get_project(
        db=db,
        project_id=project_id,
        owner_id=current_user.id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project


# ============================================================
# DELETE PROJECT
# ============================================================

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project_endpoint(
    project_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    project = get_project(
        db=db,
        project_id=project_id,
        owner_id=current_user.id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    delete_project(
        db=db,
        project=project,
    )


# ============================================================
# UPDATE PROJECT
# ============================================================

@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
)
def update_project_endpoint(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    project = get_project(
        db=db,
        project_id=project_id,
        owner_id=current_user.id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return update_project(
        db=db,
        project=project,
        name=project_data.name,
        description=project_data.description,
    )
