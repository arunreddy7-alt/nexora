from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.agent_output import AgentOutput
from backend.app.agents.ceo_agent import run_ceo_agent
from backend.app.agents.pm_agent import run_pm_agent
from backend.app.agents.architect_agent import run_architect_agent
from backend.app.agents.developer_agent import run_developer_agent

def create_agent_output(
    db: Session,
    project_id: int,
    agent_type: str,
    output: dict[str, Any],
    version: int = 1,
) -> AgentOutput:
    agent_output = AgentOutput(
        project_id=project_id,
        agent_type=agent_type,
        output=output,
        version=version,
    )

    db.add(agent_output)
    db.commit()
    db.refresh(agent_output)

    return agent_output
def get_project_agent_outputs(
    db: Session,
    project_id: int,
) -> list[AgentOutput]:
    return (
        db.query(AgentOutput)
        .filter(AgentOutput.project_id == project_id)
        .order_by(AgentOutput.created_at.asc())
        .all()
    )
def run_and_save_ceo_agent(
    db: Session,
    project_id: int,
    project_description: str,
) -> AgentOutput:
    output = run_ceo_agent(project_description)

    agent_output = AgentOutput(
        project_id=project_id,
        agent_type="CEO",
        output=output,
        version=1,
    )

    db.add(agent_output)
    db.commit()
    db.refresh(agent_output)

    return agent_output
def run_and_save_pm_agent(
    db: Session,
    project_id: int,
) -> AgentOutput:
    ceo_output = (
        db.query(AgentOutput)
        .filter(
            AgentOutput.project_id == project_id,
            AgentOutput.agent_type == "CEO",
        )
        .order_by(AgentOutput.created_at.desc())
        .first()
    )

    if ceo_output is None:
        raise ValueError("CEO output not found for this project")

    output = run_pm_agent(ceo_output.output)

    pm_output = AgentOutput(
        project_id=project_id,
        agent_type="PM",
        output=output,
        version=1,
    )

    db.add(pm_output)
    db.commit()
    db.refresh(pm_output)

    return pm_output
def run_and_save_architect_agent(
    db: Session,
    project_id: int,
) -> AgentOutput:
    pm_output = (
        db.query(AgentOutput)
        .filter(
            AgentOutput.project_id == project_id,
            AgentOutput.agent_type == "PM",
        )
        .order_by(AgentOutput.created_at.desc())
        .first()
    )

    if pm_output is None:
        raise ValueError("PM output not found for this project")

    output = run_architect_agent(pm_output.output)

    architect_output = AgentOutput(
        project_id=project_id,
        agent_type="ARCHITECT",
        output=output,
        version=1,
    )

    db.add(architect_output)
    db.commit()
    db.refresh(architect_output)

    return architect_output
def run_and_save_developer_agent(
    db: Session,
    project_id: int,
) -> AgentOutput:
    architect_output = (
        db.query(AgentOutput)
        .filter(
            AgentOutput.project_id == project_id,
            AgentOutput.agent_type == "ARCHITECT",
        )
        .order_by(AgentOutput.created_at.desc())
        .first()
    )

    if architect_output is None:
        raise ValueError("Architect output not found for this project")

    output = run_developer_agent(architect_output.output)

    developer_output = AgentOutput(
        project_id=project_id,
        agent_type="DEVELOPER",
        output=output,
        version=1,
    )

    db.add(developer_output)
    db.commit()
    db.refresh(developer_output)

    return developer_output