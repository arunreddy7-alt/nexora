from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


WORKSPACE_ROOT = (
    Path(__file__).resolve().parents[3] / "workspaces"
)

EXCLUDED_DIRECTORIES = {
    "node_modules",
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}

EXCLUDED_FILES = {
    ".DS_Store",
}


def get_project_workspace(project_id: int) -> Path:
    workspace = WORKSPACE_ROOT / f"project_{project_id}"

    if not workspace.exists():
        raise FileNotFoundError(
            f"Workspace does not exist: {workspace}"
        )

    return workspace.resolve()


def create_project_zip(
    project_id: int,
) -> Path:

    workspace = get_project_workspace(
        project_id
    )

    zip_path = (
        WORKSPACE_ROOT
        / f"project_{project_id}.zip"
    )

    if zip_path.exists():
        zip_path.unlink()

    with ZipFile(
        zip_path,
        "w",
        ZIP_DEFLATED,
    ) as zip_file:

        for file_path in workspace.rglob("*"):

            if not file_path.is_file():
                continue

            relative_path = file_path.relative_to(
                workspace
            )

            parts = set(relative_path.parts)

            if parts.intersection(
                EXCLUDED_DIRECTORIES
            ):
                continue

            if file_path.name in EXCLUDED_FILES:
                continue

            zip_file.write(
                file_path,
                arcname=relative_path,
            )

    return zip_path