from typing import Any

from backend.app.agents.project_modifier_agent import (
    run_project_modifier,
)
from backend.app.services.workspace_service import (
    get_project_files,
    get_project_workspace,
    validate_file_path,
)
from backend.app.services.execution_service import (
    install_project_dependencies,
    run_project_tests,
    run_project_build,
)


def apply_project_modifications(
    project_id: int,
    modifier_output: dict[str, Any],
) -> dict[str, Any]:

    workspace = get_project_workspace(
        project_id
    )

    updated_files = []
    created_files = []
    deleted_files = []

    # ==================================================
    # UPDATE FILES
    # ==================================================

    for file_data in modifier_output.get(
        "files_to_update",
        [],
    ):

        file_path = file_data.get("path")
        content = file_data.get("content")

        if not file_path:
            raise ValueError(
                "Modifier returned an update without a path."
            )

        if content is None:
            raise ValueError(
                f"Modifier returned no content for: {file_path}"
            )

        relative_path = validate_file_path(
            file_path
        )

        target = (
            workspace / relative_path
        ).resolve()

        try:
            target.relative_to(
                workspace.resolve()
            )
        except ValueError:
            raise ValueError(
                f"File escapes workspace: {file_path}"
            )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            content,
            encoding="utf-8",
        )

        updated_files.append(
            file_path
        )

    # ==================================================
    # CREATE FILES
    # ==================================================

    for file_data in modifier_output.get(
        "files_to_create",
        [],
    ):

        file_path = file_data.get("path")
        content = file_data.get("content")

        if not file_path:
            raise ValueError(
                "Modifier returned a create without a path."
            )

        if content is None:
            raise ValueError(
                f"Modifier returned no content for: {file_path}"
            )

        relative_path = validate_file_path(
            file_path
        )

        target = (
            workspace / relative_path
        ).resolve()

        try:
            target.relative_to(
                workspace.resolve()
            )
        except ValueError:
            raise ValueError(
                f"File escapes workspace: {file_path}"
            )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            content,
            encoding="utf-8",
        )

        created_files.append(
            file_path
        )

    # ==================================================
    # DELETE FILES
    # ==================================================

    for file_data in modifier_output.get(
        "files_to_delete",
        [],
    ):

        if isinstance(file_data, dict):
            file_path = file_data.get("path")
        else:
            file_path = file_data

        if not file_path:
            continue

        relative_path = validate_file_path(
            file_path
        )

        target = (
            workspace / relative_path
        ).resolve()

        try:
            target.relative_to(
                workspace.resolve()
            )
        except ValueError:
            raise ValueError(
                f"File escapes workspace: {file_path}"
            )

        if target.exists() and target.is_file():
            target.unlink()
            deleted_files.append(
                file_path
            )

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


def modify_existing_project(
    project_id: int,
    instruction: str,
) -> dict[str, Any]:

    if not instruction or not instruction.strip():
        raise ValueError(
            "Modification instruction cannot be empty."
        )

    current_files = get_project_files(
        project_id
    )

    if not current_files:
        raise ValueError(
            "Project workspace is empty."
        )

    modifier_output = run_project_modifier(
        files=current_files,
        instruction=instruction.strip(),
    )

    if not isinstance(
        modifier_output,
        dict,
    ):
        raise ValueError(
            "Modifier returned an invalid response."
        )

    changes = apply_project_modifications(
        project_id=project_id,
        modifier_output=modifier_output,
    )

    dependencies_changed = bool(
        modifier_output.get(
            "dependencies_changed",
            False,
        )
    )

    execution = {}

    # ==================================================
    # DEPENDENCIES
    # ==================================================

    if dependencies_changed:
        execution["install"] = (
            install_project_dependencies(
                project_id
            )
        )

    # ==================================================
    # TEST
    # ==================================================

    test_result = run_project_tests(
        project_id
    )

    execution["test"] = test_result

    # ==================================================
    # BUILD
    # ==================================================

    build_result = run_project_build(
        project_id
    )

    execution["build"] = build_result

    return {
        "project_id": project_id,
        "instruction": instruction,
        "modifier": modifier_output,
        "changes": changes,
        "execution": execution,
        "success": build_result.get(
            "success",
            False,
        ),
    }