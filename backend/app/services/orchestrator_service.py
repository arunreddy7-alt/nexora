import json
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.pipeline_run import PipelineRun

from backend.app.services.execution_service import (
    install_project_dependencies,
    run_project_tests,
    run_project_build,
)

from backend.app.services.agent_output_service import (
    run_and_save_ceo_agent,
    run_and_save_pm_agent,
    run_and_save_architect_agent,
    run_and_save_developer_agent,
)

from backend.app.services.workspace_service import (
    write_project_files,
)

from backend.app.agents.fixer_agent import (
    run_fixer_agent,
)

from backend.app.services.fixer_service import (
    apply_fixer_changes,
)

from backend.app.services.preview_service import (
    start_project_preview,
)


MAX_FIX_ATTEMPTS = 3
MAX_FIXER_CONTEXT_CHARS = 50000


# ============================================================
# SERIALIZE AGENT OUTPUT
# ============================================================

def serialize_agent_output(agent_output):
    return {
        "id": agent_output.id,
        "project_id": agent_output.project_id,
        "agent_type": agent_output.agent_type,
        "output": agent_output.output,
        "version": agent_output.version,
        "created_at": agent_output.created_at,
    }


# ============================================================
# VALIDATE GENERATED FILES
# ============================================================

def validate_generated_files(
    developer_output: dict,
) -> None:

    files = developer_output.get(
        "files",
        [],
    )

    if not isinstance(files, list):
        raise ValueError(
            "Developer output must contain a valid files list."
        )

    if not files:
        raise ValueError(
            "Developer Agent did not generate any files."
        )

    for file_data in files:

        if not isinstance(file_data, dict):
            raise ValueError(
                "Developer output contains an invalid file entry."
            )

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

        if not isinstance(content, str):
            raise ValueError(
                f"Generated file content must be a string: {file_path}"
            )

        # ----------------------------------------------------
        # Validate JSON files
        # ----------------------------------------------------

        if Path(file_path).suffix.lower() == ".json":

            try:
                json.loads(content)

            except json.JSONDecodeError as exc:

                raise ValueError(
                    "Generated JSON file is invalid: "
                    f"{file_path}. "
                    f"Line {exc.lineno}, "
                    f"column {exc.colno}: "
                    f"{exc.msg}"
                ) from exc

        # ----------------------------------------------------
        # Validate package.json
        # ----------------------------------------------------

        if Path(file_path).name.lower() == "package.json":

            try:
                package_data = json.loads(content)

            except json.JSONDecodeError as exc:

                raise ValueError(
                    "Generated package.json is invalid. "
                    f"Line {exc.lineno}, "
                    f"column {exc.colno}: "
                    f"{exc.msg}"
                ) from exc

            if not isinstance(package_data, dict):
                raise ValueError(
                    "Generated package.json must contain "
                    "a JSON object."
                )

            if "scripts" in package_data:

                if not isinstance(
                    package_data["scripts"],
                    dict,
                ):
                    raise ValueError(
                        "package.json 'scripts' must be an object."
                    )


# ============================================================
# NORMALIZE GENERATED PROJECT CONFIGURATION
# ============================================================

def normalize_project_configuration(
    developer_output: dict,
) -> dict:
    """
    Normalize deterministic project configuration.

    Vite scripts are added when needed.

    Tailwind/PostCSS are NOT injected automatically.
    """

    files = developer_output.get(
        "files",
        [],
    )

    if not isinstance(files, list):
        return developer_output

    package_file = None

    for file_data in files:

        if not isinstance(file_data, dict):
            continue

        file_path = file_data.get(
            "path",
            "",
        )

        if Path(file_path).name.lower() == "package.json":

            package_file = file_data
            break

    if package_file is None:
        return developer_output

    try:

        package_data = json.loads(
            package_file.get(
                "content",
                "",
            )
        )

    except json.JSONDecodeError:

        return developer_output

    if not isinstance(package_data, dict):
        return developer_output

    dependencies = package_data.get(
        "dependencies",
        {},
    )

    dev_dependencies = package_data.get(
        "devDependencies",
        {},
    )

    if not isinstance(
        dependencies,
        dict,
    ):
        dependencies = {}

    if not isinstance(
        dev_dependencies,
        dict,
    ):
        dev_dependencies = {}

    all_dependencies = {
        **dependencies,
        **dev_dependencies,
    }

    dependency_text = json.dumps(
        all_dependencies
    ).lower()

    file_names = {
        Path(
            item.get(
                "path",
                "",
            )
        ).name.lower()

        for item in files

        if isinstance(
            item,
            dict,
        )
    }

    # ========================================================
    # DETECT VITE
    # ========================================================

    has_vite_config = bool(
        file_names.intersection(
            {
                "vite.config.ts",
                "vite.config.js",
                "vite.config.mjs",
                "vite.config.cjs",
            }
        )
    )

    is_vite_project = (
        "vite" in dependency_text
        or has_vite_config
    )

    if is_vite_project:

        scripts = package_data.get(
            "scripts",
            {},
        )

        if not isinstance(
            scripts,
            dict,
        ):
            scripts = {}

        scripts.setdefault(
            "dev",
            "vite",
        )

        scripts.setdefault(
            "build",
            "vite build",
        )

        scripts.setdefault(
            "preview",
            "vite preview",
        )

        package_data["scripts"] = scripts

    # ========================================================
    # WRITE NORMALIZED PACKAGE.JSON
    # ========================================================

    package_file["content"] = json.dumps(
        package_data,
        indent=2,
    )

    return developer_output


# ============================================================
# READ WORKSPACE FILES
# ============================================================

def get_workspace_files(
    project_id: int,
    max_total_chars: int = MAX_FIXER_CONTEXT_CHARS,
) -> list[dict]:

    workspace = (
        Path(__file__).resolve().parents[3]
        / "workspaces"
        / f"project_{project_id}"
    )

    if not workspace.exists():
        raise FileNotFoundError(
            f"Workspace does not exist: {workspace}"
        )

    files = []
    total_chars = 0

    ignored_directories = {
        "node_modules",
        ".git",
        "dist",
        "build",
        ".next",
        "coverage",
        "__pycache__",
        ".venv",
    }

    ignored_files = {
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
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

        if path.name in ignored_files:
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

        remaining_chars = (
            max_total_chars - total_chars
        )

        if remaining_chars <= 0:
            break

        if len(content) > remaining_chars:
            content = content[:remaining_chars]

        files.append(
            {
                "path": relative_path.as_posix(),
                "content": content,
            }
        )

        total_chars += len(content)

    return files


# ============================================================
# FULL AGENT PIPELINE
# ============================================================

def run_full_agent_pipeline(
    db: Session,
    project_id: int,
    project_description: str,
):

    pipeline_run = PipelineRun(
        project_id=project_id,
        status="QUEUED",
        current_agent=None,
    )

    db.add(pipeline_run)
    db.commit()
    db.refresh(pipeline_run)

    preview_result = None

    try:

        # ==================================================
        # CEO
        # ==================================================

        pipeline_run.status = "CEO_RUNNING"
        pipeline_run.current_agent = "CEO"
        pipeline_run.started_at = datetime.utcnow()

        db.commit()

        ceo_output = run_and_save_ceo_agent(
            db=db,
            project_id=project_id,
            project_description=project_description,
        )

        # ==================================================
        # PM
        # ==================================================

        pipeline_run.status = "PM_RUNNING"
        pipeline_run.current_agent = "PM"

        db.commit()

        pm_output = run_and_save_pm_agent(
            db=db,
            project_id=project_id,
        )

        # ==================================================
        # ARCHITECT
        # ==================================================

        pipeline_run.status = "ARCHITECT_RUNNING"
        pipeline_run.current_agent = "ARCHITECT"

        db.commit()

        architect_output = run_and_save_architect_agent(
            db=db,
            project_id=project_id,
        )

        # ==================================================
        # DEVELOPER
        # ==================================================

        pipeline_run.status = "DEVELOPER_RUNNING"
        pipeline_run.current_agent = "DEVELOPER"

        db.commit()

        developer_output = run_and_save_developer_agent(
            db=db,
            project_id=project_id,
        )

        # ==================================================
        # VALIDATION
        # ==================================================

        pipeline_run.status = "VALIDATING_FILES"
        pipeline_run.current_agent = "FILE_VALIDATOR"

        db.commit()

        developer_data = developer_output.output

        validate_generated_files(
            developer_data
        )

        # ==================================================
        # NORMALIZE CONFIGURATION
        # ==================================================

        developer_data = normalize_project_configuration(
            developer_data
        )

        # ==================================================
        # WRITE WORKSPACE
        # ==================================================

        pipeline_run.status = "BUILDING_WORKSPACE"
        pipeline_run.current_agent = "WORKSPACE"

        db.commit()

        generated_files = developer_data.get(
            "files",
            [],
        )

        workspace_result = write_project_files(
            project_id=project_id,
            files=generated_files,
        )

        # ==================================================
        # INSTALL DEPENDENCIES
        # ==================================================

        pipeline_run.status = "INSTALLING_DEPENDENCIES"
        pipeline_run.current_agent = "PACKAGE_INSTALLER"

        db.commit()

        install_result = install_project_dependencies(
            project_id=project_id,
        )

        if not install_result["success"]:

            raise RuntimeError(
                "Project dependency installation failed: "
                + install_result["install"]["stderr"][:1000]
            )

        # ==================================================
        # TEST + BUILD + FIX LOOP
        # ==================================================

        execution_history = []

        fix_attempts = 0
        build_success = False

        while fix_attempts <= MAX_FIX_ATTEMPTS:

            # --------------------------------------------------
            # TEST
            # --------------------------------------------------

            pipeline_run.status = "TESTING"
            pipeline_run.current_agent = "TEST_RUNNER"

            db.commit()

            test_result = run_project_tests(
                project_id=project_id,
            )

            # --------------------------------------------------
            # BUILD
            # --------------------------------------------------

            pipeline_run.status = "BUILDING"
            pipeline_run.current_agent = "BUILD_RUNNER"

            db.commit()

            build_result = run_project_build(
                project_id=project_id,
            )

            current_execution = {
                "attempt": fix_attempts,
                "tests": test_result,
                "build": build_result,
            }

            execution_history.append(
                current_execution
            )

            build_success = build_result.get(
                "success",
                False,
            )

            print(
                f"[PIPELINE] Build success: {build_success}"
            )

            if build_success:
                break

            if fix_attempts >= MAX_FIX_ATTEMPTS:
                break

            # --------------------------------------------------
            # FIXER
            # --------------------------------------------------

            pipeline_run.status = "FIXING"
            pipeline_run.current_agent = "FIXER"

            db.commit()

            current_files = get_workspace_files(
                project_id=project_id,
            )

            fixer_result = run_fixer_agent(
                files=current_files,
                execution_result=current_execution,
            )

            apply_result = apply_fixer_changes(
                project_id=project_id,
                fixer_output=fixer_result,
            )

            execution_history[-1]["fixer"] = {
                "diagnosis": fixer_result.get(
                    "diagnosis",
                    {},
                ),
                "changes": apply_result,
            }

            fix_attempts += 1

        # ==================================================
        # PREVIEW
        # ==================================================

        pipeline_run.status = "STARTING_PREVIEW"
        pipeline_run.current_agent = "PREVIEW"

        db.commit()

        print(
            f"[PREVIEW] Attempting preview for project "
            f"{project_id}"
        )

        print(
            f"[PREVIEW] Build success: {build_success}"
        )

        if build_success:

            try:

                preview_result = start_project_preview(
                    project_id=project_id,
                )

                print(
                    f"[PREVIEW] Result: {preview_result}"
                )

            except Exception as exc:

                print(
                    f"[PREVIEW] FAILED: {exc}"
                )

                preview_result = {
                    "project_id": project_id,
                    "status": "FAILED",
                    "url": None,
                    "port": None,
                    "error": str(exc),
                }

        else:

            print(
                "[PREVIEW] Skipped because the project "
                "did not successfully build."
            )

            preview_result = {
                "project_id": project_id,
                "status": "BUILD_FAILED",
                "url": None,
                "port": None,
                "error": (
                    "Preview was not started because "
                    "the production build failed."
                ),
            }

        # ==================================================
        # FINAL STATUS
        # ==================================================

        if build_success:

            pipeline_run.status = "COMPLETED"

        else:

            pipeline_run.status = "FAILED"

            pipeline_run.error_message = (
                "Project failed after "
                f"{fix_attempts} fix attempts."
            )

        pipeline_run.current_agent = None
        pipeline_run.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(pipeline_run)

        # ==================================================
        # FINAL RESPONSE
        # ==================================================

        return {
            "pipeline_run": {
                "id": pipeline_run.id,
                "project_id": pipeline_run.project_id,
                "status": pipeline_run.status,
                "current_agent": pipeline_run.current_agent,
                "started_at": pipeline_run.started_at,
                "completed_at": pipeline_run.completed_at,
            },

            "ceo": serialize_agent_output(
                ceo_output
            ),

            "pm": serialize_agent_output(
                pm_output
            ),

            "architect": serialize_agent_output(
                architect_output
            ),

            "developer": serialize_agent_output(
                developer_output
            ),

            "workspace": workspace_result,

            "execution": {
                "success": build_success,
                "fix_attempts": fix_attempts,
                "history": execution_history,
            },

            "preview": preview_result,
        }

    except Exception as exc:

        pipeline_run.status = "FAILED"
        pipeline_run.current_agent = None
        pipeline_run.error_message = str(exc)[:1000]
        pipeline_run.completed_at = datetime.utcnow()

        db.commit()

        raise