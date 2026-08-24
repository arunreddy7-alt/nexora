from pathlib import Path
import json
import subprocess
from typing import Any


# ============================================================
# ALLOWED COMMANDS
# ============================================================

ALLOWED_COMMANDS = {
    "npm install",
    "npm install --no-audit --no-fund",
    "npm ci",
    "npm ci --no-audit --no-fund",
    "npm test",
    "npm run test",
    "npm run build",
    "npm start",
}


# ============================================================
# TIMEOUTS
# ============================================================

INSTALL_TIMEOUT = 300
TEST_TIMEOUT = 120
BUILD_TIMEOUT = 180


# ============================================================
# WORKSPACE
# ============================================================

def get_workspace(project_id: int) -> Path:
    workspace = (
        Path(__file__).resolve().parents[3]
        / "workspaces"
        / f"project_{project_id}"
    )

    if not workspace.exists():
        raise FileNotFoundError(
            f"Workspace does not exist: {workspace}"
        )

    return workspace.resolve()


# ============================================================
# COMMAND VALIDATION
# ============================================================

def validate_command(command: str) -> None:
    command = command.strip()

    if command not in ALLOWED_COMMANDS:
        raise ValueError(
            f"Command is not allowed: {command}"
        )


# ============================================================
# RUN COMMAND
# ============================================================

def run_command(
    workspace: Path,
    command: str,
    timeout: int = 120,
) -> dict[str, Any]:

    validate_command(command)

    print(f"[EXEC] Starting: {command}")
    print(f"[EXEC] Directory: {workspace}")
    print(f"[EXEC] Timeout: {timeout}s")

    process = None

    try:
        process = subprocess.Popen(
            command,
            cwd=workspace,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        try:
            stdout, _ = process.communicate(
                timeout=timeout
            )

        except subprocess.TimeoutExpired:

            print(
                f"[EXEC] TIMEOUT: {command} "
                f"after {timeout}s"
            )

            # Kill npm and all child processes on Windows.
            if process.poll() is None:

                try:
                    subprocess.run(
                        [
                            "taskkill",
                            "/F",
                            "/T",
                            "/PID",
                            str(process.pid),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                except Exception:
                    pass

            try:
                stdout, _ = process.communicate(
                    timeout=10
                )
            except Exception:
                stdout = ""

            return {
                "command": command,
                "return_code": -1,
                "success": False,
                "stdout": stdout or "",
                "stderr": (
                    f"Command timed out after "
                    f"{timeout} seconds."
                ),
            }

        return_code = process.returncode

        print(
            f"[EXEC] Finished: {command} "
            f"(exit={return_code})"
        )

        output = stdout or ""

        # npm writes useful information to stdout.
        return {
            "command": command,
            "return_code": return_code,
            "success": return_code == 0,
            "stdout": output,
            "stderr": "",
        }

    except Exception as exc:

        print(
            f"[EXEC] ERROR: {command}: {exc}"
        )

        if process is not None:

            try:
                if process.poll() is None:
                    subprocess.run(
                        [
                            "taskkill",
                            "/F",
                            "/T",
                            "/PID",
                            str(process.pid),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
            except Exception:
                pass

        return {
            "command": command,
            "return_code": -1,
            "success": False,
            "stdout": "",
            "stderr": str(exc),
        }


# ============================================================
# PACKAGE.JSON
# ============================================================

def get_package_json(
    project_id: int,
) -> dict[str, Any] | None:

    workspace = get_workspace(project_id)

    package_json = workspace / "package.json"

    if not package_json.exists():
        return None

    try:
        data = json.loads(
            package_json.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(data, dict):
            return None

        return data

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return None


# ============================================================
# NODE MODULES CHECK
# ============================================================

def has_node_modules(
    workspace: Path,
) -> bool:

    node_modules = workspace / "node_modules"

    if not node_modules.exists():
        return False

    if not node_modules.is_dir():
        return False

    try:
        return any(
            node_modules.iterdir()
        )
    except OSError:
        return False


# ============================================================
# DEPENDENCY INSTALLATION
# ============================================================

def install_project_dependencies(
    project_id: int,
) -> dict[str, Any]:

    workspace = get_workspace(project_id)

    package_json = workspace / "package.json"

    if not package_json.exists():

        return {
            "stage": "install",
            "success": True,
            "skipped": True,
            "message": (
                "No package.json found. "
                "Dependency installation skipped."
            ),
        }

    # --------------------------------------------------------
    # If dependencies are already installed, don't reinstall.
    # --------------------------------------------------------

    if has_node_modules(workspace):

        print(
            "[EXEC] node_modules already exists. "
            "Skipping npm installation."
        )

        return {
            "stage": "install",
            "success": True,
            "skipped": True,
            "reason": (
                "node_modules already exists."
            ),
            "install": {
                "command": None,
                "return_code": 0,
                "success": True,
                "stdout": "",
                "stderr": "",
            },
        }

    # --------------------------------------------------------
    # Select npm ci when package-lock exists.
    # Otherwise npm install.
    # --------------------------------------------------------

    package_lock = (
        workspace / "package-lock.json"
    )

    if package_lock.exists():

        command = (
            "npm ci --no-audit --no-fund"
        )

    else:

        command = (
            "npm install --no-audit --no-fund"
        )

    print(
        "[EXEC] Installing dependencies:"
    )
    print(
        f"[EXEC] {command}"
    )

    install_result = run_command(
        workspace=workspace,
        command=command,
        timeout=INSTALL_TIMEOUT,
    )

    return {
        "stage": "install",
        "success": install_result["success"],
        "skipped": False,
        "install": install_result,
    }


# ============================================================
# TEST SCRIPT DETECTION
# ============================================================

def has_test_script(
    project_id: int,
) -> bool:

    package_data = get_package_json(
        project_id
    )

    if not package_data:
        return False

    scripts = package_data.get(
        "scripts",
        {},
    )

    if not isinstance(
        scripts,
        dict,
    ):
        return False

    test_script = scripts.get(
        "test"
    )

    if not isinstance(
        test_script,
        str,
    ):
        return False

    return bool(
        test_script.strip()
    )


# ============================================================
# RUN PROJECT TESTS
# ============================================================

def run_project_tests(
    project_id: int,
) -> dict[str, Any]:

    workspace = get_workspace(
        project_id
    )

    if not has_test_script(
        project_id
    ):

        print(
            "[EXEC] No test script. "
            "Skipping tests."
        )

        return {
            "stage": "test",
            "success": True,
            "skipped": True,
            "reason": (
                "No test script found in "
                "package.json. Testing skipped."
            ),
            "test": {
                "command": None,
                "return_code": 0,
                "success": True,
                "stdout": "",
                "stderr": "",
            },
        }

    test_result = run_command(
        workspace=workspace,
        command="npm test",
        timeout=TEST_TIMEOUT,
    )

    return {
        "stage": "test",
        "success": test_result["success"],
        "skipped": False,
        "test": test_result,
    }


# ============================================================
# BUILD SCRIPT DETECTION
# ============================================================

def has_build_script(
    project_id: int,
) -> bool:

    package_data = get_package_json(
        project_id
    )

    if not package_data:
        return False

    scripts = package_data.get(
        "scripts",
        {},
    )

    if not isinstance(
        scripts,
        dict,
    ):
        return False

    build_script = scripts.get(
        "build"
    )

    if not isinstance(
        build_script,
        str,
    ):
        return False

    return bool(
        build_script.strip()
    )


# ============================================================
# RUN PROJECT BUILD
# ============================================================

def run_project_build(
    project_id: int,
) -> dict[str, Any]:

    workspace = get_workspace(
        project_id
    )

    if not has_build_script(
        project_id
    ):

        print(
            "[EXEC] Build script missing."
        )

        return {
            "stage": "build",
            "success": False,
            "skipped": False,
            "build": {
                "command": "npm run build",
                "return_code": 1,
                "success": False,
                "stdout": "",
                "stderr": (
                    "Generated project does not contain "
                    "a 'build' script in package.json."
                ),
            },
        }

    build_result = run_command(
        workspace=workspace,
        command="npm run build",
        timeout=BUILD_TIMEOUT,
    )

    return {
        "stage": "build",
        "success": build_result["success"],
        "skipped": False,
        "build": build_result,
    }