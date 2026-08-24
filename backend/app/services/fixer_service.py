from pathlib import Path
from typing import Any

from backend.app.agents.fixer_agent import run_fixer_agent


WORKSPACE_ROOT = (
    Path(__file__).resolve().parents[3] / "workspaces"
)


def get_project_workspace(project_id: int) -> Path:
    workspace = (
        WORKSPACE_ROOT / f"project_{project_id}"
    )

    if not workspace.exists():
        raise FileNotFoundError(
            f"Workspace does not exist: {workspace}"
        )

    return workspace.resolve()


def validate_path(
    workspace: Path,
    file_path: str,
) -> Path:

    path = Path(file_path)

    if path.is_absolute():
        raise ValueError(
            f"Absolute paths are not allowed: {file_path}"
        )

    if ".." in path.parts:
        raise ValueError(
            f"Path traversal is not allowed: {file_path}"
        )

    if ":" in file_path:
        raise ValueError(
            f"Drive paths are not allowed: {file_path}"
        )

    target = (
        workspace / path
    ).resolve()

    try:
        target.relative_to(
            workspace.resolve()
        )
    except ValueError:
        raise ValueError(
            f"File escapes workspace: {file_path}"
        )

    return target


def apply_fixer_changes(
    project_id: int,
    fixer_output: dict[str, Any],
) -> dict[str, Any]:

    workspace = get_project_workspace(
        project_id
    )

    updated_files = []
    created_files = []
    deleted_files = []

    # -----------------------------------------
    # UPDATE FILES
    # -----------------------------------------

    for file_data in fixer_output.get(
        "files_to_update",
        [],
    ):

        file_path = file_data.get("path")
        content = file_data.get("content")

        if not file_path:
            raise ValueError(
                "Fixer returned an update without a path."
            )

        if content is None:
            raise ValueError(
                f"Fixer returned no content for: {file_path}"
            )

        target = validate_path(
            workspace,
            file_path,
        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            content,
            encoding="utf-8",
        )

        updated_files.append(file_path)

    # -----------------------------------------
    # CREATE FILES
    # -----------------------------------------

    for file_data in fixer_output.get(
        "files_to_create",
        [],
    ):

        file_path = file_data.get("path")
        content = file_data.get("content")

        if not file_path:
            raise ValueError(
                "Fixer returned a create without a path."
            )

        if content is None:
            raise ValueError(
                f"Fixer returned no content for: {file_path}"
            )

        target = validate_path(
            workspace,
            file_path,
        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            content,
            encoding="utf-8",
        )

        created_files.append(file_path)

    # -----------------------------------------
    # DELETE FILES
    # -----------------------------------------

    for file_path in fixer_output.get(
        "files_to_delete",
        [],
    ):

        target = validate_path(
            workspace,
            file_path,
        )

        if target.exists():

            if target.is_file():
                target.unlink()

            deleted_files.append(file_path)

    return {
        "project_id": project_id,
        "updated_files": updated_files,
        "created_files": created_files,
        "deleted_files": deleted_files,
        "total_changes": (
            len(updated_files)
            + len(created_files)
            + len(deleted_files)
        ),
    }


def fix_project(
    project_id: int,
    files: list[dict],
    execution_result: dict[str, Any],
) -> dict[str, Any]:

    fixer_output = run_fixer_agent(
        files=files,
        execution_result=execution_result,
    )

    changes = apply_fixer_changes(
        project_id=project_id,
        fixer_output=fixer_output,
    )

    return {
        "fixer": fixer_output,
        "changes": changes,
    }