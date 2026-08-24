from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import (
    get_current_user,
    get_db,
)

from backend.app.services.project_modifier_service import (
    modify_existing_project,
)

from backend.app.services.preview_service import (
    start_project_preview,
    get_project_preview,
    stop_project_preview,
)

from backend.app.models.user import User
from backend.app.models.pipeline_run import PipelineRun
from backend.app.models.project import Project

from backend.app.schemas.agent_output import (
    AgentOutputResponse,
)

from backend.app.services.agent_output_service import (
    create_agent_output,
    get_project_agent_outputs,
    run_and_save_ceo_agent,
    run_and_save_pm_agent,
    run_and_save_architect_agent,
    run_and_save_developer_agent,
)

from backend.app.services.project_service import (
    get_project,
)

from backend.app.services.orchestrator_service import (
    run_full_agent_pipeline,
)

from backend.app.services.workspace_service import (
    get_project_files,
)


router = APIRouter(
    prefix="/projects/{project_id}/agent-outputs",
    tags=["Agent Outputs"],
)


# ==========================================================
# CREATE AGENT OUTPUT
# ==========================================================

@router.post(
    "",
    response_model=AgentOutputResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_output(
    project_id: int,
    agent_type: str,
    output: dict[str, Any],
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
            detail="Project not found",
        )

    return create_agent_output(
        db=db,
        project_id=project_id,
        agent_type=agent_type,
        output=output,
    )


# ==========================================================
# GET AGENT OUTPUTS
# ==========================================================

@router.get(
    "",
    response_model=list[AgentOutputResponse],
)
def get_outputs(
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
            detail="Project not found",
        )

    return get_project_agent_outputs(
        db=db,
        project_id=project_id,
    )


# ==========================================================
# RUN CEO
# ==========================================================

@router.post(
    "/run-ceo",
    response_model=AgentOutputResponse,
    status_code=status.HTTP_201_CREATED,
)
def run_ceo(
    project_id: int,
    project_description: str,
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
            detail="Project not found",
        )

    return run_and_save_ceo_agent(
        db=db,
        project_id=project_id,
        project_description=project_description,
    )


# ==========================================================
# RUN PM
# ==========================================================

@router.post(
    "/run-pm",
    response_model=AgentOutputResponse,
    status_code=status.HTTP_201_CREATED,
)
def run_pm(
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
            detail="Project not found",
        )

    try:

        return run_and_save_pm_agent(
            db=db,
            project_id=project_id,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ==========================================================
# RUN ARCHITECT
# ==========================================================

@router.post(
    "/run-architect",
    response_model=AgentOutputResponse,
    status_code=status.HTTP_201_CREATED,
)
def run_architect(
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
            detail="Project not found",
        )

    try:

        return run_and_save_architect_agent(
            db=db,
            project_id=project_id,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ==========================================================
# RUN DEVELOPER
# ==========================================================

@router.post(
    "/run-developer",
    response_model=AgentOutputResponse,
    status_code=status.HTTP_201_CREATED,
)
def run_developer(
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
            detail="Project not found",
        )

    try:

        return run_and_save_developer_agent(
            db=db,
            project_id=project_id,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

# ==========================================================
# MODIFY EXISTING PROJECT
# ==========================================================

@router.post(
    "/modify",
)
def modify_project(
    project_id: int,
    instruction: str,
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
            detail="Project not found",
        )

    if not instruction.strip():
        raise HTTPException(
            status_code=400,
            detail="Modification instruction cannot be empty.",
        )

    try:

        return modify_existing_project(
            project_id=project_id,
            instruction=instruction,
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Project modification failed: {exc}",
        )


# ==========================================================
# RUN FULL PIPELINE
# ==========================================================

@router.post(
    "/run-pipeline",
    status_code=status.HTTP_201_CREATED,
)
def run_pipeline(
    project_id: int,
    project_description: str,
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
            detail="Project not found",
        )

    return run_full_agent_pipeline(
        db=db,
        project_id=project_id,
        project_description=project_description,
    )


# ==========================================================
# GET PIPELINE STATUS
# ==========================================================

@router.get(
    "/pipeline/{pipeline_run_id}"
)
def get_pipeline_status(
    pipeline_run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    pipeline_run = (
        db.query(PipelineRun)
        .join(
            Project,
            Project.id == PipelineRun.project_id,
        )
        .filter(
            PipelineRun.id == pipeline_run_id,
            Project.owner_id == current_user.id,
        )
        .first()
    )

    if pipeline_run is None:

        raise HTTPException(
            status_code=404,
            detail="Pipeline run not found",
        )

    return {
        "id": pipeline_run.id,
        "project_id": pipeline_run.project_id,
        "status": pipeline_run.status,
        "current_agent": pipeline_run.current_agent,
        "error_message": pipeline_run.error_message,
        "started_at": pipeline_run.started_at,
        "completed_at": pipeline_run.completed_at,
        "created_at": pipeline_run.created_at,
    }


# ==========================================================
# GET GENERATED PROJECT WORKSPACE
# ==========================================================

@router.get(
    "/workspace"
)
def get_workspace(
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
            detail="Project not found",
        )

    try:

        files = get_project_files(
            project_id=project_id
        )

    except FileNotFoundError:

        raise HTTPException(
            status_code=404,
            detail="Project workspace not found",
        )

    return {
        "project_id": project_id,
        "files_count": len(files),
        "files": files,
    }
@router.post(
    "/preview",
)
def start_preview(
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
            detail="Project not found",
        )

    try:
        return start_project_preview(
            project_id=project_id,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get(
    "/preview",
)
def preview_status(
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
            detail="Project not found",
        )

    return get_project_preview(
        project_id=project_id,
    )


@router.delete(
    "/preview",
)
def stop_preview(
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
            detail="Project not found",
        )

    stop_project_preview(
        project_id=project_id,
    )

    return {
        "project_id": project_id,
        "status": "STOPPED",
    }