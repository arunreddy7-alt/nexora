from pathlib import Path
from typing import Any


WORKSPACE_ROOT = (
    Path(__file__).resolve().parents[3] / "workspaces"
)


def get_project_workspace(project_id: int) -> Path:
    """
    Return the isolated workspace directory for a project.
    """

    workspace = WORKSPACE_ROOT / f"project_{project_id}"

    workspace.mkdir(
        parents=True,
        exist_ok=True,
    )

    return workspace


def validate_file_path(file_path: str) -> Path:
    """
    Validate a generated file path.

    Prevents the AI from writing outside the
    project workspace.
    """

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

    return path


def write_project_files(
    project_id: int,
    files: list[dict[str, Any]],
) -> dict[str, Any]:

    workspace = get_project_workspace(project_id)

    created_files = []

    for file_data in files:

        file_path = file_data.get("path")
        content = file_data.get("content")

        if not file_path:
            raise ValueError(
                "Generated file is missing a path."
            )

        if content is None:
            raise ValueError(
                f"Generated file has no content: {file_path}"
            )

        relative_path = validate_file_path(
            file_path
        )

        target_path = (
            workspace / relative_path
        ).resolve()

        try:
            target_path.relative_to(
                workspace.resolve()
            )
        except ValueError:
            raise ValueError(
                f"File escapes workspace: {file_path}"
            )

        target_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target_path.write_text(
            content,
            encoding="utf-8",
        )

        created_files.append(
            {
                "path": file_path,
                "absolute_path": str(target_path),
            }
        )

    return {
        "workspace": str(workspace),
        "project_id": project_id,
        "files_created": len(created_files),
        "files": created_files,
    }


def get_project_files(
    project_id: int,
) -> list[dict[str, Any]]:

    workspace = get_project_workspace(
        project_id
    )

    files = []

    ignored_directories = {
        "node_modules",
        ".git",
        ".next",
        "dist",
        "build",
        "coverage",
        "__pycache__",
        ".venv",
    }

    for path in workspace.rglob("*"):

        if not path.is_file():
            continue

        relative_path = path.relative_to(
            workspace
        )

        if any(
            part in ignored_directories
            for part in relative_path.parts
        ):
            continue

        try:
            content = path.read_text(
                encoding="utf-8"
            )
        except (
            UnicodeDecodeError,
            OSError,
        ):
            continue

        files.append(
            {
                "path": relative_path.as_posix(),
                "content": content,
            }
        )

    files.sort(
        key=lambda file: file["path"]
    )

    return files